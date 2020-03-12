# Device42 Ansible Inventory

This is to parse Device42 CMDB information to create a dynamic inventory for Ansible Tower.

## Installation

Use pip to install requirements that may not exist. This was written in Python 3.7.X

```bash
pip install -r requirements.txt
```

## Usage

The script is intended for usage within Ansible Tower and ran as a one-time or scheduled task to update inventories.\n
See [Custom Inventory Scripts](https://docs.ansible.com/ansible-tower/latest/html/administration/custom_inventory_script.html) for more information regarding the setup of the Ansible Tower side.

## Example output
An example for both of the outputs can be found in this repo. 

The file device42_output.json is a stripped down example of the Device42 API output.

The file ansible_inventory_output.json is the output that will be printed to Ansible Tower and then used to build the inventory. 

See [Developing dynamic inventory](https://docs.ansible.com/ansible/latest/dev_guide/developing_inventory.html#developing-inventory-scripts) for the format that Ansible expects




## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
