"""
Azure POC: Cross-Tenant Access using Workload Identity Federation
=================================================================
NO client secrets. Uses GitHub Actions OIDC token to authenticate
to multiple Azure AD tenants.

How cross-tenant works with federation:
  1. Multi-tenant app registered in Tenant A (AzureADMultipleOrgs)
  2. Federated credential trusts GitHub Actions OIDC issuer
  3. Tenant B admin consents to the app + assigns RBAC
  4. GitHub Action logs into Tenant A, then Tenant B -- no secrets

AWS Comparison:
  AWS:   sts.assume_role(RoleArn=...) -> temp credentials
  Azure: azure/login(tenant_id=TENANT_B) -> OIDC exchange, no secrets at all
"""

import os
from azure.identity import DefaultAzureCredential, ClientAssertionCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient


def list_tenant_resources(credential, label: str):
    """List subscriptions and resource groups using given credential."""
    print(f"\n{'=' * 60}")
    print(f"Accessing: {label}")
    print("=" * 60)

    try:
        sub_client = SubscriptionClient(credential)
        subscriptions = list(sub_client.subscriptions.list())
        print(f"Found {len(subscriptions)} subscription(s):")

        for sub in subscriptions:
            print(f"\n  Subscription: {sub.display_name} ({sub.subscription_id})")
            resource_client = ResourceManagementClient(credential, sub.subscription_id)
            rgs = list(resource_client.resource_groups.list())
            if rgs:
                for rg in rgs[:5]:
                    print(f"    RG: {rg.name} ({rg.location})")
                if len(rgs) > 5:
                    print(f"    ... and {len(rgs) - 5} more")
            else:
                print("    (no resource groups)")
    except Exception as e:
        print(f"  Error: {e}")
        print("  Checklist:")
        print("    1. Admin consent granted in target tenant?")
        print("    2. RBAC role assigned in target subscription?")
        print("    3. Federated credential configured for this repo?")


def main():
    print("=" * 60)
    print("Cross-Tenant Access via Workload Identity Federation")
    print("(No client secret used!)")
    print("=" * 60)

    home_tenant = os.environ.get("HOME_TENANT_ID")
    foreign_tenant = os.environ.get("FOREIGN_TENANT_ID")

    if not home_tenant:
        print("\nMissing HOME_TENANT_ID. Set it in the workflow env.")
        return

    # DefaultAzureCredential picks up the OIDC token from azure/login
    credential = DefaultAzureCredential()
    print("\nAuthenticated via Workload Identity Federation (OIDC)")

    # Access Home Tenant
    list_tenant_resources(credential, f"HOME Tenant ({home_tenant})")

    # Access Foreign Tenant
    if foreign_tenant and foreign_tenant != home_tenant:
        # For cross-tenant: the workflow must run azure/login again
        # with tenant-id set to FOREIGN_TENANT_ID. Each login step
        # produces a new DefaultAzureCredential context.
        print(f"\n{'=' * 60}")
        print("CROSS-TENANT NOTE")
        print("=" * 60)
        print("To access Tenant B, the workflow runs a second azure/login")
        print("step with tenant-id=FOREIGN_TENANT_ID. This script would")
        print("then run under that context automatically.")
        print(f"Foreign Tenant ID: {foreign_tenant}")
        list_tenant_resources(credential, f"FOREIGN Tenant ({foreign_tenant})")
    else:
        client_id = os.environ.get("AZURE_CLIENT_ID", "<app-id>")
        print(f"\n{'=' * 60}")
        print("FOREIGN Tenant (not configured yet)")
        print("=" * 60)
        print("When Tenant B is available, an admin there runs:")
        print(f"  az ad sp create --id {client_id}")
        print(f"  az role assignment create --assignee {client_id} \\")
        print(f"    --role Reader --scope /subscriptions/<SUB_ID>")
        print("Then update the workflow with FOREIGN_TENANT_ID.")
        print("No code or credential changes needed.")

    print(f"\n{'=' * 60}")
    print("POC Complete! Zero secrets used.")
    print("=" * 60)


if __name__ == "__main__":
    main()
