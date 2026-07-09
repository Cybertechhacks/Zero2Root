# Mobile Security — Android

!!! info "Why This Matters"
    Android penetration testing follows the OWASP MASTG — the most structured mobile testing standard. Interviewers probe your setup knowledge (they know it's complex), your understanding of the Android security model, and your ability to bypass certificate pinning (the single most common question in mobile pentest interviews).

---

## Android Architecture — Security Perspective

Understanding Android's architecture is essential because every vulnerability maps back to a misuse or bypass of one of these layers.

### Linux Kernel (Layer 1)
Android is built on Linux. Each application runs under a unique Linux user ID (UID) — this is the foundation of Android's sandboxing. App isolation is enforced at the OS level, not application level.

### Hardware Abstraction Layer (HAL)
Interfaces between Linux kernel and higher layers. Vendor-specific implementations. Relevant for hardware-backed key storage (StrongBox, TEE).

### Android Runtime (ART) — Layer 3
Replaces Dalvik (pre-5.0). Compiles `.dex` (Dalvik Executable) bytecode. `.dex` files are compiled Java/Kotlin code. ART uses AOT (Ahead-of-Time) compilation in modern Android.

**Relevance:** `.dex` files can be decompiled back to readable Java with tools like jadx. App logic is *never* truly hidden unless native code (C/C++ via NDK) is used.

### Framework Layer
Core Android APIs: Activity Manager, Package Manager, Resource Manager, Location Manager, etc. Application components (Activity, Service, Broadcast Receiver, Content Provider) are defined here. Misconfigured components are a major attack surface.

### Application Layer
User-installed apps. Run in sandboxed processes with unique UIDs. Cannot directly access each other's data (unless sharing the same signing key and sharedUserId, which is a legacy mechanism).

---

## APK Structure — What's Inside

An APK is a ZIP file. Everything inside is accessible to an attacker.

```
app.apk (ZIP)
├── AndroidManifest.xml    — Application configuration (decoded: permissions, components, exported)
├── classes.dex            — Compiled application code (primary)
├── classes2.dex           — Additional DEX files (multidex apps)
├── res/                   — Resources (layouts, strings, drawables)
│   └── values/strings.xml — Hardcoded strings — API keys, URLs, secrets often here
├── assets/                — Raw assets — databases, config files, scripts
├── lib/                   — Native libraries (.so files)
│   ├── arm64-v8a/
│   └── armeabi-v7a/
├── META-INF/              — Signing information
│   ├── MANIFEST.MF        — List of all files and their hashes
│   └── CERT.RSA           — App signing certificate
└── resources.arsc         — Compiled resource table
```

**AndroidManifest.xml** is the most critical file for initial static analysis:
```xml
<manifest package="com.example.app">
    
    <!-- Permissions requested -->
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.READ_CONTACTS"/>
    
    <application
        android:debuggable="true"     ← CRITICAL: debuggable in production = high finding
        android:allowBackup="true"    ← Medium: backup allows data extraction
        android:networkSecurityConfig="@xml/network_security_config">
        
        <!-- Activities -->
        <activity android:name=".MainActivity" android:exported="true">
            <!-- exported=true + no permission = accessible by any app -->
        </activity>
        
        <!-- Exported with intent filter (implicit export) -->
        <activity android:name=".WebViewActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.VIEW"/>
                <data android:scheme="https" android:host="*"/>
            </intent-filter>
        </activity>
        
        <!-- Services -->
        <service android:name=".SyncService" android:exported="false"/>
        <!-- exported=false: only accessible within same app -->
        
        <!-- Content Providers -->
        <provider android:name=".DataProvider"
                  android:authorities="com.example.app.provider"
                  android:exported="true"    ← dangerous if not properly protected
                  android:readPermission="com.example.READ"/>
        
        <!-- Broadcast Receivers -->
        <receiver android:name=".UpdateReceiver" android:exported="true"/>
        <!-- exported receiver without permission = any app can trigger it -->
        
    </application>
</manifest>
```

---

## OWASP MASTG Testing Categories

The Mobile Application Security Testing Guide (MASTG) with the MASVS (Mobile Application Security Verification Standard) defines what to test. Key categories for Android:

### MASVS-STORAGE — Insecure Data Storage

**Testing locations:**
```bash
# Connect device (USB debugging enabled or rooted device)
adb devices

# App private data directory (requires root or adb shell as app UID)
adb shell run-as com.example.app
ls /data/data/com.example.app/

# Common storage locations:
# /data/data/com.example.app/shared_prefs/   → SharedPreferences XML files
# /data/data/com.example.app/databases/      → SQLite databases
# /data/data/com.example.app/files/          → Files
# /data/data/com.example.app/cache/          → Cache

# Pull app data to local machine
adb backup -noapk com.example.app -f backup.ab
# Note: backup can be disabled via android:allowBackup="false"

# Check SharedPreferences for sensitive data
adb shell run-as com.example.app cat shared_prefs/*.xml

# Pull SQLite databases and examine
adb pull /data/data/com.example.app/databases/app.db ./
sqlite3 app.db
sqlite> .tables
sqlite> SELECT * FROM users;
sqlite> SELECT * FROM tokens;

# Check external storage
adb shell ls /sdcard/Android/data/com.example.app/

# Logcat — apps often log sensitive data
adb logcat | grep -iE "(password|token|key|secret|credential|auth)"
```

**Common findings:**
- Cleartext credentials in SharedPreferences
- Unencrypted SQLite database with user data
- Sensitive data in log files (debug logging left in production)
- Session tokens stored in external storage
- Sensitive data in app cache
- Cleartext HTTP traffic captured in network cache

### MASVS-CRYPTO — Cryptography

```java
// Common insecure patterns to look for in decompiled code:

// 1. Hardcoded encryption keys
byte[] key = "mysecretkey12345".getBytes();

// 2. ECB mode (insecure block cipher mode)
Cipher.getInstance("AES/ECB/PKCS5Padding");  // ECB leaks patterns

// 3. Hardcoded IV
byte[] iv = new byte[16];  // All-zero IV with CBC = insecure

// 4. Weak/deprecated algorithms
Cipher.getInstance("DES");           // DES is broken
MessageDigest.getInstance("MD5");    // MD5 is broken for security
MessageDigest.getInstance("SHA-1");  // SHA-1 broken for collisions

// 5. Insecure random number generator
Random rand = new Random();         // Predictable
// Should use: SecureRandom secureRand = new SecureRandom();

// 6. Custom cryptography (always wrong)
// Look for home-grown XOR or rotation ciphers
```

### MASVS-AUTH — Authentication and Session Management

```bash
# Test session token storage
adb shell run-as com.example.app cat shared_prefs/auth.xml

# Test token expiration — use an old token from weeks ago
# Test token invalidation on logout

# Check for biometric bypass
# If app uses biometric auth, test:
# 1. Frida hook to bypass biometric check
# 2. Use adb fingerprint simulation (on emulator)
adb -e emu finger touch 1   # Simulate fingerprint on emulator

# Check for root/emulator detection bypass (to test auth in instrumented environment)
```

### MASVS-NETWORK — Network Communication

```bash
# Set up proxy:
# Device proxy → Burp Suite on attacker machine
# For HTTP: adb shell settings put global http_proxy attacker_ip:8080

# Install Burp CA cert
adb push burp_ca.der /sdcard/burp_ca.der
# Device: Settings → Security → Install certificates

# Check Network Security Config for cleartext permissions
# AndroidManifest.xml → android:networkSecurityConfig
cat res/xml/network_security_config.xml

# Dangerous config:
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">example.com</domain>
    </domain-config>
    <base-config cleartextTrafficPermitted="true"/>  ← Allows HTTP globally
</network-security-config>
```

---

## Static Analysis

### APK Extraction and Decompilation

```bash
# Method 1: Pull from device
adb shell pm path com.example.app
# Output: package:/data/app/com.example.app-xxx/base.apk
adb pull /data/app/com.example.app-xxx/base.apk

# Method 2: Download from APKPure/APKMirror
# Use: https://apkpure.com/

# Decompile with jadx (best Java decompiler)
jadx -d output_dir/ app.apk
# Or jadx-gui for UI
jadx-gui app.apk

# Decompile with apktool (for smali and resources)
apktool d app.apk -o output_dir/

# apktool gives:
# - smali/ (Dalvik assembly — lower level than jadx Java)
# - AndroidManifest.xml (decoded)
# - res/ (decoded resources)
```

### MobSF — Automated Static Analysis

```bash
# Docker setup
docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest

# Access: http://localhost:8000
# Upload APK → automated analysis
# Covers: manifest issues, hardcoded secrets, dangerous API usage, permissions

# Key sections to review:
# - Android Manifest Analysis (exported components, permissions)
# - Security Analysis (insecure code patterns)
# - File Analysis (interesting files in APK)
# - Strings Analysis (potential hardcoded secrets)
# - Permissions Analysis
```

### Manual Source Code Review (jadx output)

```bash
# Key search patterns in decompiled code:

# Hardcoded secrets
grep -r "api_key\|apikey\|secret\|password\|token\|AWS\|Bearer" output_dir/

# HTTP URLs (cleartext traffic)
grep -r "http://" output_dir/

# Logging sensitive data
grep -r "Log\.d\|Log\.v\|Log\.i\|Log\.e\|System\.out\.print" output_dir/

# Insecure crypto
grep -r "ECB\|DES\|MD5\|SHA-1\|Random()" output_dir/

# WebView JavaScript enabled
grep -r "setJavaScriptEnabled(true)\|addJavascriptInterface" output_dir/

# Exported components with no permission
grep -r "exported=\"true\"" output_dir/AndroidManifest.xml

# SQL queries (potential SQLi in local DB)
grep -r "rawQuery\|execSQL" output_dir/

# Dynamic code loading
grep -r "DexClassLoader\|PathClassLoader\|loadClass" output_dir/

# SSL pinning implementation (to understand what to bypass)
grep -r "checkServerTrusted\|CertificatePinner\|TrustManager\|hostnameVerifier" output_dir/

# Firebase URLs (often publicly accessible)
grep -r "firebaseio.com\|firebase.google.com" output_dir/
```

---

## Dynamic Analysis

### ADB Basics

```bash
# Device management
adb devices                    # List connected devices
adb shell                      # Shell on device
adb shell -s emulator-5554     # Specific device

# App management
adb install app.apk
adb uninstall com.example.app
adb shell pm list packages -f   # List installed packages with paths
adb shell pm path com.example.app  # APK path

# File operations
adb push local_file /sdcard/
adb pull /data/data/com.example.app/databases/app.db ./

# Logcat
adb logcat                              # All logs
adb logcat -s MyApp:D                   # Tag-filtered
adb logcat | grep -i "password\|token"  # Grep for sensitive strings
adb logcat > app_logs.txt              # Save to file

# Activity/intent testing
adb shell am start -n com.example.app/.MainActivity
adb shell am start -a android.intent.action.VIEW -d "https://example.com" com.example.app
# Test deep links and exported activities

# Broadcast testing
adb shell am broadcast -a com.example.app.ACTION_UPDATE -n com.example.app/.UpdateReceiver
```

### Frida — Dynamic Instrumentation

Frida injects JavaScript into a running process to hook and modify function calls in real time.

```bash
# Setup
# Install frida-tools on attacker
pip install frida-tools

# Push frida-server to device
adb push frida-server-16.x.x-android-arm64 /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server
adb shell /data/local/tmp/frida-server &

# Verify
frida-ps -U  # List processes on USB-connected device

# Basic usage
frida -U -f com.example.app -l script.js --no-pause
# -U = USB device, -f = spawn app, -l = load script
```

**Frida script examples:**

```javascript
// Hook a specific Java method
Java.perform(function() {
    var MainActivity = Java.use('com.example.app.MainActivity');
    
    MainActivity.login.implementation = function(username, password) {
        console.log('[*] Login called with username: ' + username + ' password: ' + password);
        return this.login(username, password); // Call original
    };
});

// Hook all methods in a class
Java.perform(function() {
    var TargetClass = Java.use('com.example.app.CryptoUtils');
    TargetClass.decrypt.implementation = function(data) {
        var result = this.decrypt(data);
        console.log('[*] Decrypt input: ' + data);
        console.log('[*] Decrypt output: ' + result);
        return result;
    };
});

// Hook system API calls
Java.perform(function() {
    // Hook SharedPreferences to capture all reads/writes
    var SharedPreferences = Java.use('android.app.SharedPreferencesImpl');
    SharedPreferences.getString.implementation = function(key, defValue) {
        var result = this.getString(key, defValue);
        console.log('[SharedPrefs] getString(' + key + ') = ' + result);
        return result;
    };
});
```

### Objection — Frida Automation Framework

Objection automates common mobile testing tasks using Frida.

```bash
# Launch app with objection
objection -g com.example.app explore

# Inside objection console:

# File system exploration
android hooking list activities       # List activities
android hooking list classes          # All loaded classes
android hooking search classes ssl    # Search for SSL-related classes

# Memory inspection
memory dump all /tmp/memdump.bin
memory search "password" utf8

# Jobs — hook and monitor
android hooking watch class com.example.app.CryptoUtil   # Watch all methods
android hooking watch method com.example.app.Auth.checkPin   # Watch specific method

# Root detection bypass
android root disable                 # Disable root detection hooks
android root simulate                # Simulate non-rooted environment

# SSL pinning bypass
android sslpinning disable           # Disable all SSL pinning

# SQLite database inspection
android sqlite databases list
android sqlite execute "SELECT * FROM users"
```

---

## Certificate Pinning Bypass

Certificate pinning is the most commonly tested technique in mobile interview questions. Always be ready to explain what it is, why it's there, and at least 3 ways to bypass it.

### What Is Certificate Pinning?

Normal TLS: app trusts any certificate signed by a CA in the device's trust store. Installing Burp's CA certificate on the device makes the app trust Burp's MITM certificate.

Certificate pinning: the app hardcodes one or more expected certificates or public keys. Even if a trusted CA issues a certificate, if it doesn't match the pinned value, the connection is rejected.

**Purpose:** Prevent MITM even if a CA is compromised or a test device has a rogue CA installed.

### Bypass Technique 1: Objection (Automated)

```bash
objection -g com.example.app explore
android sslpinning disable

# Under the hood: hooks TrustManager, OkHttp CertificatePinner,
# Conscrypt, Xamarin, Flutter, React Native — most common pinning implementations
```

### Bypass Technique 2: Frida Script

```javascript
// Universal SSL Unpinning script (hooks multiple pinning implementations)
// From: https://codeshare.frida.re/@pcipolloni/universal-android-ssl-pinning-bypass-with-frida/

setTimeout(function() {
    Java.perform(function() {
        // Hook OkHttp3 CertificatePinner
        try {
            var CertificatePinner = Java.use('okhttp3.CertificatePinner');
            CertificatePinner.check.overload('java.lang.String', 'java.util.List')
                .implementation = function(hostname, peerCertificates) {
                    console.log('[*] OkHttp3 CertificatePinner bypassed for: ' + hostname);
                    return; // Skip the check
                };
        } catch(e) {}
        
        // Hook TrustManager
        try {
            var TrustManager = Java.registerClass({
                name: 'com.attack.TrustManager',
                implements: [Java.use('javax.net.ssl.X509TrustManager')],
                methods: {
                    checkClientTrusted: function(chain, authType) {},
                    checkServerTrusted: function(chain, authType) {},
                    getAcceptedIssuers: function() { return []; }
                }
            });
            // Install the custom TrustManager
        } catch(e) {}
        
        console.log('[*] SSL Pinning disabled');
    });
}, 0);
```

```bash
# Run with frida
frida -U -f com.example.app -l ssl_bypass.js --no-pause
```

### Bypass Technique 3: APK Modification

```bash
# 1. Decompile with apktool
apktool d app.apk -o app_decoded/

# 2. Locate Network Security Config
cat app_decoded/res/xml/network_security_config.xml

# 3. Add user-trusted CAs and disable pinning
cat > app_decoded/res/xml/network_security_config.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config>
        <trust-anchors>
            <certificates src="system"/>
            <certificates src="user"/>  <!-- Trust user-installed CAs (Burp) -->
        </trust-anchors>
    </base-config>
    <!-- Remove all <pin-set> elements that enforce pinning -->
</network-security-config>
EOF

# 4. Repackage
apktool b app_decoded/ -o app_modified.apk

# 5. Sign the modified APK (required to install)
keytool -genkeypair -v -keystore test.jks -alias testkey -keyalg RSA -keysize 2048 -validity 365
apksigner sign --ks test.jks --out app_signed.apk app_modified.apk

# 6. Install
adb install -r app_signed.apk
```

### Bypass Technique 4: Xposed/LSPosed

Install Xposed framework on rooted device, then SSL Unpinning module (TrustMeAlready, JustTrustMe). These hook the Android framework at the OS level — no per-app modification needed.

### Bypass Technique 5: Root + Custom Trust Store

On a rooted device, add Burp's certificate to the system trust store:
```bash
# Convert Burp cert to PEM
openssl x509 -inform DER -in burp_ca.der -out burp_ca.pem

# Calculate hash for Android system cert naming
HASH=$(openssl x509 -inform PEM -subject_hash_old -in burp_ca.pem | head -1)
cp burp_ca.pem $HASH.0

# Mount system as writable and add cert
adb root
adb remount
adb push $HASH.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/$HASH.0
adb reboot
```

---

## Common Android Vulnerabilities Summary

| Vulnerability | Finding Location | Severity |
|---------------|-----------------|----------|
| Hardcoded API keys | APK strings, source code | High–Critical |
| Debuggable in production | AndroidManifest.xml | High |
| Exported components | AndroidManifest.xml | Medium–High |
| Cleartext traffic | network_security_config.xml, HTTP traffic | Medium–High |
| Insecure data storage (cleartext SQLite/SharedPrefs) | /data/data/... | High |
| Weak cryptography | Decompiled source code | High |
| Sensitive data in logs | Logcat output | Medium–High |
| Missing certificate pinning | Network traffic interception | Medium |
| Backup enabled | AndroidManifest.xml | Low–Medium |
| Root detection bypass | Dynamic analysis | Informational |
| Deep link injection | AndroidManifest.xml + source code | Medium–High |
| WebView remote code execution | Source code (addJavascriptInterface) | Critical |
