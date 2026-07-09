# Mobile Testing Tools

!!! info "Purpose"
    Deep reference for Android and iOS security testing tools. Covers the complete testing workflow from static analysis through dynamic instrumentation.

---

## ADB — Android Debug Bridge

The primary interface to an Android device during testing.

### Device Management

```bash
# List connected devices
adb devices
# Output: device serial number + state (device/unauthorized/offline)

# Shell on specific device (when multiple connected)
adb -s emulator-5554 shell
adb -s R3CN90FXXX shell

# USB vs TCP/IP connection
adb tcpip 5555                    # Switch device to TCP mode
adb connect 192.168.1.100:5555    # Connect over Wi-Fi
adb disconnect                    # Disconnect TCP connection

# Device info
adb shell getprop ro.product.model         # Device model
adb shell getprop ro.build.version.release # Android version
adb shell getprop ro.build.version.sdk     # API level
adb shell getprop ro.product.cpu.abi       # Architecture
```

### App Management

```bash
# List installed packages
adb shell pm list packages                # All packages
adb shell pm list packages -3             # Third-party only
adb shell pm list packages -f             # With APK path
adb shell pm list packages | grep example # Filter by name

# Get APK path
adb shell pm path com.example.app
# Output: package:/data/app/com.example.app-xxx/base.apk

# Pull APK from device
adb pull /data/app/com.example.app-xxx/base.apk ./app.apk

# Install APK
adb install app.apk
adb install -r app.apk              # Reinstall (keep data)
adb install -d app.apk              # Allow downgrade

# Uninstall
adb uninstall com.example.app
adb uninstall -k com.example.app    # Keep data

# Start specific activity
adb shell am start -n com.example.app/.MainActivity
adb shell am start -n com.example.app/.LoginActivity

# Test deep links
adb shell am start -a android.intent.action.VIEW \
  -d "https://app.example.com/reset?token=test" \
  com.example.app

# Send broadcast
adb shell am broadcast -a com.example.app.ACTION_UPDATE
```

### File Operations

```bash
# Download from device
adb pull /data/data/com.example.app/shared_prefs/prefs.xml ./
adb pull /data/data/com.example.app/databases/app.db ./
adb pull /sdcard/Download/ ./downloads/

# Upload to device
adb push ./payload /data/local/tmp/payload
adb shell chmod 755 /data/local/tmp/payload

# Access app private data (non-root, via run-as)
adb shell run-as com.example.app ls /data/data/com.example.app/
adb shell run-as com.example.app cat /data/data/com.example.app/shared_prefs/prefs.xml

# App data directories to check:
# /data/data/com.example.app/shared_prefs/  → SharedPreferences XML
# /data/data/com.example.app/databases/     → SQLite databases
# /data/data/com.example.app/files/         → App files
# /data/data/com.example.app/cache/         → Cache
# /sdcard/Android/data/com.example.app/     → External storage
```

### Logging and Monitoring

```bash
# All logcat output
adb logcat

# Filter by tag
adb logcat -s MyApp:D

# Filter by priority (V/D/I/W/E/F)
adb logcat *:W                       # Warnings and above only

# Grep for sensitive strings
adb logcat | grep -iE "password|token|key|secret|credential|api"

# Save logs to file
adb logcat > app_logs.txt

# Clear logcat buffer
adb logcat -c

# Show log with timestamps
adb logcat -v time

# Monitor specific process
PID=$(adb shell pidof com.example.app)
adb logcat --pid=$PID

# Network traffic monitoring (combine with tcpdump on device)
adb shell tcpdump -i any -s 0 -w /sdcard/capture.pcap
adb pull /sdcard/capture.pcap ./
# Open in Wireshark
```

### Proxy Setup for Traffic Interception

```bash
# Method 1: System proxy (HTTP/HTTPS)
adb shell settings put global http_proxy 192.168.1.50:8080
adb shell settings delete global http_proxy   # Remove proxy

# Method 2: Wi-Fi proxy (manual on device)
# Settings → Wi-Fi → Long press network → Modify → Advanced → Proxy

# Install Burp CA certificate
# Export Burp cert: Proxy → Options → Export CA Certificate → DER format
adb push burp_ca.der /sdcard/burp_ca.der
# On device: Settings → Security → Install from storage → select file
# Android 11+: Settings → Security → More security settings → Encryption & credentials

# Verify proxy is working
adb shell settings get global http_proxy
```

### Port Forwarding

```bash
# Forward device port to host (access device service from computer)
adb forward tcp:8080 tcp:8080

# Reverse forward (access computer service from device)
adb reverse tcp:9090 tcp:9090

# List forwards
adb forward --list
adb reverse --list

# Remove forward
adb forward --remove tcp:8080

# Common use case: Frida server port
adb forward tcp:27042 tcp:27042
```

---

## apktool — APK Decompilation and Repackaging

```bash
# Decompile APK
apktool d app.apk -o output_dir/

# Decompile with specific options
apktool d app.apk -o output_dir/ --no-res    # Skip resource decoding
apktool d app.apk -o output_dir/ --force     # Overwrite if exists
apktool d app.apk -o output_dir/ -r          # No resource decoding (faster)
apktool d app.apk -o output_dir/ --only-main-classes  # Only main DEX

# Output structure:
# output_dir/
# ├── AndroidManifest.xml   ← Decoded manifest
# ├── apktool.yml           ← Build metadata
# ├── res/                  ← Decoded resources
# │   └── values/
# │       └── strings.xml   ← String values including URLs, keys
# ├── smali/                ← Disassembled Dalvik bytecode
# └── lib/                  ← Native libraries

# Rebuild APK after modification
apktool b output_dir/ -o app_modified.apk
apktool b output_dir/ -o app_modified.apk --use-aapt2

# Generate signing keystore
keytool -genkeypair -v \
  -keystore test.jks \
  -alias testkey \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000 \
  -storepass password \
  -keypass password \
  -dname "CN=Test,O=Test,C=US"

# Sign APK
apksigner sign \
  --ks test.jks \
  --ks-key-alias testkey \
  --ks-pass pass:password \
  --key-pass pass:password \
  --out app_signed.apk \
  app_modified.apk

# Verify signature
apksigner verify app_signed.apk

# Install signed APK
adb install -r app_signed.apk
```

### What to Look For in apktool Output

```bash
# 1. AndroidManifest.xml — critical security indicators
grep -i "debuggable" output_dir/AndroidManifest.xml    # Should be false/absent
grep -i "allowBackup" output_dir/AndroidManifest.xml   # Should be false
grep -i "exported" output_dir/AndroidManifest.xml      # Note exported components
grep -i "permission" output_dir/AndroidManifest.xml    # All permissions requested
grep -i "networkSecurityConfig" output_dir/AndroidManifest.xml

# 2. Network Security Config
cat output_dir/res/xml/network_security_config.xml
# Look for: cleartextTrafficPermitted, certificate pinning config, trust anchors

# 3. Strings — hardcoded secrets
grep -ri "api" output_dir/res/values/strings.xml
grep -ri "key" output_dir/res/values/strings.xml
grep -ri "password" output_dir/res/values/strings.xml
grep -ri "http://" output_dir/res/values/strings.xml

# 4. Smali code — dangerous API usage
grep -r "getSharedPreferences\|putString\|putPassword" output_dir/smali/
grep -r "SecretKeySpec\|DESede\|AES/ECB" output_dir/smali/
grep -r "Runtime.getRuntime\|exec\b" output_dir/smali/
```

---

## jadx — Decompile APK to Java

jadx produces more readable code than apktool's smali output.

```bash
# CLI decompile
jadx -d output_dir/ app.apk

# With options
jadx -d output_dir/ app.apk \
  --deobf \                    # Attempt deobfuscation
  --show-bad-code \            # Show decompile errors inline
  --no-imports \               # Full class names (avoid ambiguity)
  --threads-count 4            # Parallel decompilation

# GUI (recommended for large codebases)
jadx-gui app.apk
# Features: file navigation, full-text search, xref (find usages)

# Decompile multiple DEX files (if multidex app)
jadx -d output_dir/ classes.dex classes2.dex classes3.dex
```

### Key Search Patterns After Decompilation

```bash
# Hardcoded credentials and secrets
grep -r "api_key\|apikey\|api-key" output_dir/ -i
grep -r "password\|passwd\|pwd" output_dir/ -i
grep -r "secret\|token\|bearer" output_dir/ -i
grep -r "AWS_\|AZURE_\|GCP_" output_dir/ -i
grep -r "firebase\|firebaseio" output_dir/ -i

# HTTP URLs (cleartext traffic)
grep -r "http://" output_dir/ | grep -v "//"  # Exclude comments

# Logging sensitive data
grep -r "Log\.d\|Log\.v\|Log\.i\|Log\.e\|Log\.w" output_dir/ | \
  grep -v "TAG" | head -50   # Show non-tag log calls

# Insecure cryptography
grep -r "AES/ECB\|DES\|RC4\|MD5\|SHA-1\b" output_dir/ -i
grep -r "SecretKeySpec\|PBEKeySpec" output_dir/
grep -r "new Random()\|Math\.random()" output_dir/

# WebView JavaScript (XSS risk)
grep -r "setJavaScriptEnabled(true)\|addJavascriptInterface" output_dir/
grep -r "loadUrl\|loadData\|evaluateJavascript" output_dir/

# File operations (path traversal risk)
grep -r "openFileInput\|FileInputStream\|new File(" output_dir/

# SSL/TLS pinning implementation (helps plan bypass)
grep -r "CertificatePinner\|TrustManager\|checkServerTrusted\|X509TrustManager" output_dir/
grep -r "hostnameVerifier\|ALLOW_ALL_HOSTNAME" output_dir/

# SQL queries (local SQLi)
grep -r "rawQuery\|execSQL\|compileStatement" output_dir/

# SharedPreferences (data storage)
grep -r "getSharedPreferences\|putString\|putInt" output_dir/

# Broadcast receivers and intents
grep -r "sendBroadcast\|onReceive\|registerReceiver" output_dir/
```

---

## MobSF — Mobile Security Framework

### Setup

```bash
# Docker (recommended)
docker pull opensecurity/mobile-security-framework-mobsf:latest
docker run -it --rm \
  -p 8000:8000 \
  -v /path/to/mobsf_data:/home/mobsf/.MobSF \
  opensecurity/mobile-security-framework-mobsf:latest

# Access: http://localhost:8000

# Local installation (Python)
git clone https://github.com/MobSF/Mobile-Security-Framework-MobSF
cd Mobile-Security-Framework-MobSF
./setup.sh    # Linux
python manage.py runserver 0.0.0.0:8000
```

### Static Analysis Workflow

```
1. Upload APK (drag-and-drop or REST API)
2. Wait for analysis (~60 seconds)
3. Review each section:

SECURITY SCORE
→ Overall risk percentage

ANDROID MANIFEST
→ Exported components (Activities, Services, Receivers, Providers)
→ Dangerous permissions
→ Backup settings, debuggable flag

SECURITY ANALYSIS
→ Code analysis findings (severity: high/warning/info/secure)
→ Each finding shows file + line number + code snippet
→ Critical patterns: hardcoded keys, insecure crypto, SQL injection, path traversal

FILE ANALYSIS
→ Interesting files detected in APK
→ Certificates, config files, SQLite databases embedded in APK

STRINGS ANALYSIS
→ All strings extracted from binary
→ Filter for: URLs, keys, tokens, emails, base64 blobs

NETWORK SECURITY
→ Network security config analysis
→ Cleartext traffic permissions
→ Domain-specific configurations

PERMISSIONS
→ Dangerous permissions mapped to what they access
→ Overprivileged app detection

CERTIFICATE ANALYSIS
→ Signing certificate details
→ Debug vs release certificate detection
```

### REST API for Automation

```bash
# Upload and scan via API
APIKEY="your_api_key"   # Set in MobSF config

# Upload APK
curl -F "file=@app.apk" http://localhost:8000/api/v1/upload \
  -H "Authorization: $APIKEY"
# Returns: {"scan_type": "apk", "hash": "abc123..."}

# Start scan
curl -X POST http://localhost:8000/api/v1/scan \
  -d "scan_type=apk&hash=abc123..." \
  -H "Authorization: $APIKEY"

# Get JSON report
curl "http://localhost:8000/api/v1/report_json?hash=abc123..." \
  -H "Authorization: $APIKEY" > report.json

# Download PDF report
curl "http://localhost:8000/api/v1/download_pdf?hash=abc123..." \
  -H "Authorization: $APIKEY" > report.pdf
```

---

## Frida — Dynamic Instrumentation

### Setup

```bash
# Install frida-tools on attacker machine
pip install frida-tools

# Find matching frida-server version
frida --version   # Note the version number

# Download frida-server for device architecture
# https://github.com/frida/frida/releases
# Choose: frida-server-{version}-android-{arch}.xz
# Common archs: arm64 (modern phones), x86_64 (emulators)

# Push and start frida-server
adb push frida-server-16.x.x-android-arm64 /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server
adb shell "/data/local/tmp/frida-server &"

# Verify
frida-ps -U                    # List processes on USB device
frida-ps -U | grep com.example # Find target app
```

### Core Usage

```bash
# Attach to running process
frida -U -n "com.example.app" -l hook_script.js

# Spawn and attach (app starts fresh)
frida -U -f com.example.app -l hook_script.js --no-pause

# Interactive REPL (no script)
frida -U -n "com.example.app"

# Run script and exit
frida -U -f com.example.app -l script.js --no-pause -q -e "run()"

# Detach after timeout
timeout 60 frida -U -f com.example.app -l script.js --no-pause
```

### Essential Frida Scripts

```javascript
// === Hook a specific Java method ===
Java.perform(function() {
    var TargetClass = Java.use("com.example.app.AuthManager");
    
    TargetClass.login.implementation = function(username, password) {
        console.log("[*] login() called");
        console.log("[*] Username: " + username);
        console.log("[*] Password: " + password);
        
        // Call original method
        var result = this.login(username, password);
        console.log("[*] Return value: " + result);
        return result;
    };
});

// === Hook overloaded method ===
Java.perform(function() {
    var Crypto = Java.use("com.example.app.CryptoUtil");
    
    // Hook specific overload
    Crypto.decrypt.overload("java.lang.String", "java.lang.String")
        .implementation = function(data, key) {
            var result = this.decrypt(data, key);
            console.log("[Decrypt] Input: " + data);
            console.log("[Decrypt] Key: " + key);
            console.log("[Decrypt] Output: " + result);
            return result;
        };
});

// === Watch all methods in a class ===
Java.perform(function() {
    var className = "com.example.app.NetworkManager";
    var TargetClass = Java.use(className);
    
    // Get all method names
    var methods = TargetClass.class.getDeclaredMethods();
    methods.forEach(function(method) {
        var methodName = method.getName();
        try {
            TargetClass[methodName].overloads.forEach(function(overload) {
                overload.implementation = function() {
                    console.log("[*] " + className + "." + methodName + "() called");
                    return overload.apply(this, arguments);
                };
            });
        } catch(e) {}
    });
});

// === Monitor SharedPreferences ===
Java.perform(function() {
    var SharedPrefsImpl = Java.use("android.app.SharedPreferencesImpl");
    
    SharedPrefsImpl.getString.implementation = function(key, defValue) {
        var result = this.getString(key, defValue);
        if (result !== null) {
            console.log("[SharedPrefs] getString(" + key + ") = " + result);
        }
        return result;
    };
    
    // Also hook Editor.putString to catch writes
    var EditorImpl = Java.use("android.app.SharedPreferencesImpl$EditorImpl");
    EditorImpl.putString.implementation = function(key, value) {
        console.log("[SharedPrefs] putString(" + key + ", " + value + ")");
        return this.putString(key, value);
    };
});

// === Hook SQLite ===
Java.perform(function() {
    var SQLiteDatabase = Java.use("android.database.sqlite.SQLiteDatabase");
    
    SQLiteDatabase.rawQuery.implementation = function(sql, selectionArgs) {
        console.log("[SQLite] Query: " + sql);
        if (selectionArgs !== null) {
            console.log("[SQLite] Args: " + selectionArgs.join(", "));
        }
        return this.rawQuery(sql, selectionArgs);
    };
    
    SQLiteDatabase.execSQL.overload("java.lang.String").implementation = function(sql) {
        console.log("[SQLite] execSQL: " + sql);
        return this.execSQL(sql);
    };
});

// === Monitor HTTP requests (OkHttp) ===
Java.perform(function() {
    var OkHttpClient = Java.use("okhttp3.OkHttpClient");
    var RealCall = Java.use("okhttp3.internal.connection.RealCall");
    
    RealCall.execute.implementation = function() {
        var request = this.request();
        console.log("[OkHttp] URL: " + request.url());
        console.log("[OkHttp] Method: " + request.method());
        
        var headers = request.headers();
        for (var i = 0; i < headers.size(); i++) {
            console.log("[OkHttp] Header: " + headers.name(i) + ": " + headers.value(i));
        }
        
        return this.execute();
    };
});
```

### SSL Pinning Bypass Scripts

```javascript
// === Universal Android SSL Pinning Bypass ===
// Hooks TrustManager, OkHttp, Conscrypt, Apache HTTP, WebViewClient

Java.perform(function() {
    // Bypass 1: TrustManager (most common)
    var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
    var SSLContext = Java.use("javax.net.ssl.SSLContext");
    
    var TrustManager = Java.registerClass({
        name: "com.frida.TrustManager",
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) { },
            checkServerTrusted: function(chain, authType) { },
            getAcceptedIssuers: function() { return []; }
        }
    });
    
    var TrustManagers = [TrustManager.$new()];
    var sslContext = SSLContext.getInstance("TLS");
    sslContext.init(null, TrustManagers, null);
    
    // Bypass 2: OkHttp3 CertificatePinner
    try {
        var CertificatePinner = Java.use("okhttp3.CertificatePinner");
        CertificatePinner.check.overload("java.lang.String", "java.util.List")
            .implementation = function(hostname, peerCertificates) {
                console.log("[Bypass] OkHttp pinning bypassed for: " + hostname);
                return;
            };
    } catch(e) {}
    
    // Bypass 3: HostnameVerifier
    try {
        var OkHostnameVerifier = Java.use("okhttp3.internal.tls.OkHostnameVerifier");
        OkHostnameVerifier.verify.overload("java.lang.String", "javax.net.ssl.SSLSession")
            .implementation = function(hostname, session) {
                return true;
            };
    } catch(e) {}
    
    console.log("[*] SSL Pinning bypass active");
});
```

---

## Objection — Automated Frida Framework

```bash
# Install
pip install objection

# Launch with target app
objection -g com.example.app explore

# Launch with frida gadget (for non-jailbroken/no root)
objection -g gadget explore
```

### Objection Command Reference

```
# === App Information ===
android info list              # App metadata, paths
android info packages          # All installed packages
ios info list                  # iOS equivalent

# === File System ===
android filesystem list        # List app file system
android filesystem download /data/data/com.example/databases/app.db
android filesystem upload ./payload /data/local/tmp/payload

# === Class and Method Hooking ===
android hooking list classes                           # All loaded classes
android hooking search classes auth                    # Search class names
android hooking list methods com.example.AuthManager  # Methods in class
android hooking watch class com.example.Crypto         # Hook all methods
android hooking watch method com.example.Auth.checkPin --dump-args --dump-return

# === Memory ===
memory list modules            # Loaded libraries
memory list exports libssl.so  # Exports from library
memory dump all /tmp/dump.bin  # Full memory dump
memory search "password" utf8  # Search for string in memory
memory write ...               # Write to memory address

# === Environment ===
env                            # App environment variables and paths

# === Keystore ===
android keystore list          # List Android KeyStore contents

# === SQLite ===
android sqlite list databases
android sqlite connect /data/data/com.example/databases/app.db
android sqlite execute "SELECT * FROM users"

# === Security Bypasses ===
android root disable           # Bypass root detection hooks
android root simulate          # Simulate non-root environment
android sslpinning disable     # Bypass SSL certificate pinning

# === iOS-Specific ===
ios keychain dump              # Dump iOS Keychain items
ios pasteboard monitor         # Monitor clipboard
ios sslpinning disable         # Bypass iOS SSL pinning
ios hooking list classes
ios hooking watch class SomeClass
ios hooking watch method '-[SomeClass someMethod]' --dump-args --dump-return

# === UI Interaction ===
android ui screenshot /tmp/screen.png
android ui alert "test"
```

---

## class-dump (iOS)

Extracts Objective-C class headers from iOS binaries.

```bash
# Install
brew install class-dump  # macOS
# or download binary from http://stevenygard.com/projects/class-dump/

# Extract headers from iOS binary
class-dump App.app/App > App_headers.h

# Organized output
class-dump -H App.app/App -o headers/

# Grep for interesting classes
grep -i "auth\|login\|password\|token\|crypt\|key" App_headers.h

# Grep for interesting methods
grep -i "checkPin\|verify\|authenticate\|encrypt\|decrypt" App_headers.h
```

---

## Quick Reference: Setup Checklists

### Android Assessment Setup

```
□ Device with USB debugging enabled
□ ADB connected: adb devices (shows device)
□ Frida server running: adb shell /data/local/tmp/frida-server &
□ frida-ps -U confirms target app process
□ Burp CA cert installed on device
□ Device proxy set to Burp listener
□ apktool installed: apktool --version
□ jadx installed: jadx --version
□ MobSF running: http://localhost:8000
□ objection installed: objection --version
```

### iOS Assessment Setup (Jailbroken)

```
□ Jailbroken device (checkra1n/palera1n/unc0ver)
□ SSH accessible: ssh mobile@device_ip
□ Frida installed via Sileo/Cydia (build.frida.re repo)
□ frida-ps -U confirms device visible
□ Burp CA cert installed (Settings → General → VPN & Device Mgmt)
□ Device proxy configured
□ class-dump available
□ objection installed: pip install objection
□ SSL Kill Switch 2 installed (via Cydia)
```
