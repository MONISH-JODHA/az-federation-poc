import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient


def main():
    print("=" * 60)
    print("Same-Tenant Access via Workload Identity Federation")
    print("=" * 60)

    credential = DefaultAzureCredential()
    print("\nAuthenticated via Workload Identity Federation (OIDC)")

    print("\n--- Accessible Subscriptions ---")
    sub_client = SubscriptionClient(credential)
    subscriptions = list(sub_client.subscriptions.list())

    if not subscriptions:
        print("  (No accessible subscriptions)")
        return

    for sub in subscriptions:
        print(f"\n  Subscription: {sub.display_name} ({sub.subscription_id})")
        print(f"  State: {sub.state}")

        print(f"\n  --- Resource Groups ---")
        resource_client = ResourceManagementClient(credential, sub.subscription_id)
        rgs = list(resource_client.resource_groups.list())
        if rgs:
            for rg in rgs:
                print(f"    - {rg.name} ({rg.location})")
        else:
            print("    (none)")

        print(f"\n  --- Virtual Machines ---")
        compute_client = ComputeManagementClient(credential, sub.subscription_id)
        vms = list(compute_client.virtual_machines.list_all())
        if vms:
            for vm in vms:
                print(f"    - {vm.name} ({vm.location})")
        else:
            print("    (none)")

    print("\n" + "=" * 60)
    print("POC Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
