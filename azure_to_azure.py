import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient


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
    label = sys.argv[1] if len(sys.argv) > 1 else "unknown"

    print("=" * 60)
    print(f"Azure-to-Azure POC: Accessing {label}")
    print("(No secrets used - OIDC federation only)")
    print("=" * 60)

    credential = DefaultAzureCredential()
    print(f"\nAuthenticated to {label} via OIDC")

    list_resources(credential, label)

    print(f"\n{'=' * 60}")
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
