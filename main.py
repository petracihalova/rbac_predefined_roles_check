import base64
import json
import logging
import os
import sys

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("roles_diff.log"), logging.StreamHandler(sys.stdout)],
)


def get_roles_from_customer_portal():
    """
    Get roles from RH Customer portal - User Access guide - table '4.1 Predefined roles provided with User Access'
    """
    table_link = "https://access.redhat.com/documentation/en-us/red_hat_hybrid_cloud_console/1-latest/html-single/user_access_configuration_guide_for_role-based_access_control_rbac/index"
    response = requests.get(table_link)

    if response.status_code != 200:
        raise requests.ConnectionError(
            f"Response code {response.status_code} returned."
        )

    soup = BeautifulSoup(response.text, "html.parser")
    html_table_with_roles = soup.find_all("table")[1]

    roles_from_customer_docs = {}
    for row in html_table_with_roles.find_all("tr"):
        row_data = [cell.text.strip() for cell in row.find_all("td")]
        if not row_data:
            continue
        name = row_data[0]
        description = row_data[1]
        platform_default = row_data[2]
        admin_default = row_data[3]
        roles_from_customer_docs[name] = {
            "name": name,
            "description": description,
            "platform_default": bool(platform_default),
            "admin_default": bool(admin_default),
        }

    logger.info("Predefined roles from RH Customer portal downloaded sucessfully\n")
    return roles_from_customer_docs


def get_roles_from_rbac_config():
    """
    Get roles from rbac-config repo
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("'GITHUB_TOKEN' variable not found")
    url = f"https://api.github.com/repos/RedHatInsights/rbac-config/contents/configs/prod/roles"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }
    params = {"ref": "master"}
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        raise requests.ConnectionError(
            f"Response code {response.status_code} returned."
        )
    configs_list = [config.get("path") for config in response.json()]

    roles_from_rbac_config = {}
    for config in configs_list:
        url = (
            f"https://api.github.com/repos/RedHatInsights/rbac-config/contents/{config}"
        )
        response = requests.get(url, params=params, headers=headers)
        content = base64.b64decode(response.json().get("content"))
        roles = json.loads(content).get("roles")
        for role in roles:
            name = role.get("display_name")
            if not name:
                name = role.get("name")
            r = {
                "name": name,
                "description": role.get("description"),
                "platform_default": bool(role.get("platform_default")),
                "admin_default": bool(role.get("admin_default")),
            }
            roles_from_rbac_config[name] = r
    logger.info("Predefined roles from 'rbac-config' downloaded sucessfully\n")
    return roles_from_rbac_config


def compare_roles(roles_from_customer_docs, roles_from_rbac_config):
    """
    Compare role list from customer documentation and rbac-config repo
    """
    for name, role_rbac_config in roles_from_rbac_config.items():
        if name in roles_from_customer_docs:
            role_customer_doc = roles_from_customer_docs[name]
            if role_rbac_config["description"] != role_customer_doc["description"]:
                message = (
                    f"Description from rbac-config (1) and Customer Documentation (2) is not same.\n"
                    f"\t(1) {role_rbac_config['description']}\n"
                    f"\t(2) {role_customer_doc['description']}\n"
                )
                logger.warning(message)
            if (
                role_rbac_config["platform_default"]
                != role_customer_doc["platform_default"]
            ):
                message = (
                    f"'Platform default' tag from rbac-config (1) and Customer Documentation (2) is not same.\n"
                    f"(1) {role_rbac_config['platform_default']}\n"
                    f"(2) {role_customer_doc['platform_default']}\n"
                )
                logger.warning(message)
            if role_rbac_config["admin_default"] != role_customer_doc["admin_default"]:
                message = (
                    f"'Admin default' tag from rbac-config (1) and Customer Documentation (2) is not same.\n"
                    f"(1) {role_rbac_config['admin_default']}\n"
                    f"(2) {role_customer_doc['admin_default']}\n"
                )
                logger.warning(message)
        else:
            logger.warning(
                f"Role '{name}' from rbac-config is not listed in the Customer Documentation.\n"
            )

    # Check if there is some role listed in the Customer Documentation and not present in the rbac-config
    for name in roles_from_customer_docs:
        if name not in roles_from_rbac_config:
            logger.warning(
                f"Role '{name}' from Customer Documentation is not listed in rbac-config repo\n"
            )


def main():
    # This is a tool for compare the Predefined RBAC roles from the RH Customer portal (link below) with
    # the rbac-config repo (https://github.com/redhatinsights/rbac-config)

    logger.info("Job started.\n")

    compare_roles(get_roles_from_customer_portal(), get_roles_from_rbac_config())

    logger.info("Job done.\n")


if __name__ == "__main__":
    main()
