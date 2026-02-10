"""
Azure POC: Same-Tenant Access using Workload Identity Federation
================================================================
NO client secrets. Uses GitHub Actions OIDC token to authenticate.

How it works:
  1. GitHub Actions requests an OIDC token from GitHub's token service
  2. azure/login@v2 exchanges that token with Azure AD
  3. Azure AD validates the token against the federated credential config
  4. Returns an Azure access token -- no secrets involved

Environment variables set by azure/login action:
  AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_SUBSCRIPTION_ID
  + OIDC token endpoint (used internally by DefaultAzureCredential)
"""

import os
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient


def main():
    print("=" * 60)
    print("Same-Tenant Access via Workload Identity Federation")
    print("(No client secret used!)")
    print("=" * 60)

    # DefaultAzureCredential automatically picks up the federated token
    # set by the azure/login GitHub Action. No secrets needed.
    credential = DefaultAzureCredential()
    print("\nAuthenticated via Workload Identity Federation (OIDC)")

    # List all accessible subscriptions
    print("\n--- Accessible Subscriptions ---")
    sub_client = SubscriptionClient(credential)
    subscriptions = list(sub_client.subscriptions.list())

    if not subscriptions:
        print("  (No accessible subscriptions)")
        return

    for sub in subscriptions:
        print(f"\n  Subscription: {sub.display_name} ({sub.subscription_id})")
        print(f"  State: {sub.state}")

        # List resource groups
        print(f"\n  --- Resource Groups ---")
        resource_client = ResourceManagementClient(credential, sub.subscription_id)
        rgs = list(resource_client.resource_groups.list())
        if rgs:
            for rg in rgs:
                print(f"    - {rg.name} ({rg.location})")
        else:
            print("    (none)")

        # List VMs
        print(f"\n  --- Virtual Machines ---")
        compute_client = ComputeManagementClient(credential, sub.subscription_id)
        vms = list(compute_client.virtual_machines.list_all())
        if vms:
            for vm in vms:
                print(f"    - {vm.name} ({vm.location})")
        else:
            print("    (none)")

    print("\n" + "=" * 60)
    print("POC Complete! No secrets were used in this authentication.")
    print("=" * 60)


if __name__ == "__main__":
    main()
