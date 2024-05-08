# Tool for comparing predefined roles from customer documentation and rbac-config
* Red Hat Customer Portal - User Access Configuration Guide for Role-based Access Control (RBAC) - Table 4.1. Predefined roles provided with User Access ([link](https://access.redhat.com/documentation/en-us/red_hat_hybrid_cloud_console/1-latest/html-single/user_access_configuration_guide_for_role-based_access_control_rbac/index#assembly-insights-rbac-reference_user-access-configuration))
* rbac-config GitHub repo ([link](https://github.com/RedHatInsights/rbac-config))

The tool compares list of predefined RBAC roles from RH customer documentation with roles from rbac-config GitHub repository. The tool compares:
* role name
* role description
* platfrom default field
* admin default field

All found differences are listed in the logs.

## How to run 
1. Create virtual environment and install dependencies
2. Save github token as env var `export GITHUB_TOKEN=<value>`
3. Run the tool `python main.py`


## How to run with podman
1. Build an image `podman build -t roles_tool .`
2. Run container `podman run --name roles-diff -e GITHUB_TOKEN=<github_token_value> roles_tool` and check logs
3. If needed, check logs again `podman logs roles_diff`
