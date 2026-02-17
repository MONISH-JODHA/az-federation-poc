import os
import requests
from azure.identity import ManagedIdentityCredential, ClientAssertionCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient


def get_mi_token(audience="api://AzureADTokenExchange"):
    credential = ManagedIdentityCredential()
    token = credential.get_token(audience)
    return token.token


def get_assertion():
    return get_mi_token()


def list_resources(credential, label: str):
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

        if not subscriptions:
            print("  (no subscriptions - tenant-level access only)")

    except Exception as e:
        print(f"  Error: {e}")


def main():
    print("=" * 60)
    print("TRUE Azure-to-Azure Access (Managed Identity -> Tenant B)")
    print("This script MUST run on an Azure VM with Managed Identity")
    print("=" * 60)

    tenant_b_id = os.environ.get("TENANT_B_ID")
    tenant_b_app_client_id = os.environ.get("TENANT_B_APP_CLIENT_ID")

    if not all([tenant_b_id, tenant_b_app_client_id]):
        print("\nMissing environment variables. Set:")
        print("  TENANT_B_ID            - Target tenant ID")
        print("  TENANT_B_APP_CLIENT_ID - App registration in Tenant B")
        return

    print("\nStep 1: Listing Tenant A resources (via Managed Identity)...")
    mi_credential = ManagedIdentityCredential()
    list_resources(mi_credential, "Tenant A (Managed Identity - local)")

    print("\nStep 2: Acquiring self-token from Managed Identity...")
    try:
        self_token = get_mi_token()
        print(f"  Self-token acquired (length: {len(self_token)} chars)")
    except Exception as e:
        print(f"  Error: {e}")
        print("  This script must run on an Azure VM with Managed Identity enabled.")
        return

    print("\nStep 3: Exchanging MI token for Tenant B access...")
    credential_b = ClientAssertionCredential(
        tenant_id=tenant_b_id,
        client_id=tenant_b_app_client_id,
        func=get_assertion,
    )

    print("\nStep 4: Accessing Tenant B resources...")
    list_resources(credential_b, f"Tenant B ({tenant_b_id})")

    print(f"\n{'=' * 60}")
    print("TRUE Azure-to-Azure POC Complete!")
    print("Managed Identity in Tenant A accessed Tenant B via token exchange.")
    print("Zero secrets used. No chained federation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
