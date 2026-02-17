import os
import json
import urllib.request
from azure.identity import ClientAssertionCredential, DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient


def get_self_token(audience="api://AzureADTokenExchange"):
    credential = DefaultAzureCredential()
    token = credential.get_token(audience)
    return token.token


def get_assertion():
    return get_self_token()


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
    except Exception as e:
        print(f"  Error: {e}")


def main():
    print("=" * 60)
    print("Azure-to-Azure Access via Workload Identity Federation")
    print("=" * 60)

    tenant_a = os.environ.get("TENANT_A_ID")
    tenant_b = os.environ.get("TENANT_B_ID")
    tenant_b_app_client_id = os.environ.get("TENANT_B_APP_CLIENT_ID")

    if not all([tenant_a, tenant_b, tenant_b_app_client_id]):
        print("\nMissing environment variables. Set:")
        print("  TENANT_A_ID            - Source tenant (where identity lives)")
        print("  TENANT_B_ID            - Target tenant (to access)")
        print("  TENANT_B_APP_CLIENT_ID - App registration in Tenant B")
        return

    print(f"\nSource: Tenant A ({tenant_a})")
    print(f"Target: Tenant B ({tenant_b})")
    print(f"Target App:      ({tenant_b_app_client_id})")

    print("\nStep 1: Acquiring self-token from Tenant A identity...")
    try:
        self_token = get_self_token()
        print("  Self-token acquired (no secrets used)")
    except Exception as e:
        print(f"  Error acquiring self-token: {e}")
        print("  This script must run from an Azure workload with Managed Identity")
        print("  or from GitHub Actions with OIDC federation configured.")
        return

    print("\nStep 2: Exchanging self-token for Tenant B access...")
    credential_b = ClientAssertionCredential(
        tenant_id=tenant_b,
        client_id=tenant_b_app_client_id,
        func=get_assertion,
    )
    print("  ClientAssertionCredential created (no secrets)")

    print("\nStep 3: Accessing Tenant B resources...")
    list_resources(credential_b, f"Tenant B ({tenant_b})")

    print(f"\n{'=' * 60}")
    print("POC Complete! Zero secrets used.")
    print("Azure Identity A accessed Azure Tenant B via token exchange.")
    print("=" * 60)


if __name__ == "__main__":
    main()
