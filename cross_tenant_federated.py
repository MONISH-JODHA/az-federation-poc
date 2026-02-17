import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient


def list_tenant_resources(credential, label: str):
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
    print("Cross-Tenant Access via Workload Identity Federation")
    print("=" * 60)

    home_tenant = os.environ.get("HOME_TENANT_ID")
    foreign_tenant = os.environ.get("FOREIGN_TENANT_ID")

    if not home_tenant:
        print("\nMissing HOME_TENANT_ID. Set it in the workflow env.")
        return

    credential = DefaultAzureCredential()
    print("\nAuthenticated via Workload Identity Federation (OIDC)")

    list_tenant_resources(credential, f"HOME Tenant ({home_tenant})")

    if foreign_tenant and foreign_tenant != home_tenant:
        list_tenant_resources(credential, f"FOREIGN Tenant ({foreign_tenant})")
    else:
        print(f"\n{'=' * 60}")
        print("FOREIGN Tenant (not configured yet)")
        print("=" * 60)

    print(f"\n{'=' * 60}")
    print("POC Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
