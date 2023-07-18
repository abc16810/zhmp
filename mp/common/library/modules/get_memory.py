#!/usr/bin/python
# -*- coding: utf-8 -*-
from ansible.module_utils.basic import AnsibleModule
import subprocess
import json
import os

# Copyright: (c) 2012, Derek Carter<goozbach@friocorte.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# from __future__ import absolute_import, division, print_function
# __metaclass__ = type

ANSIBLE_METADATA = {
	'metadata_version': '1.1',
	'status': ['preview'],
	'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: get_memory

short_description: Gathers memory deatil for hostsystem

version_added: "2.9"

description:
	- "Gets the memory details of the system"
author:
	- wsm
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  get_memory:
    name: hello world
'''


HAS_DMI = True
TMP = os.system('which dmidecode 2>/dev/null')
if TMP == 0:
	HAS_DMI = False


def get_exec_cmd(cmd):
	try:
		result = os.popen(cmd)
		res = result.readlines()
	except Exception:
		res = []
	return res


def handle_result(data):
	lines = []
	lines_raw = []
	line_in = False
	data.append('')
	for line in data:
		if not line_in and lines:
			lines_raw.append(lines)
			lines = []
			continue
		if line.startswith('Memory Device'):
			line_in = True
		if line_in:
			if line.strip():
				lines.append(line.strip())
			else:
				line_in = False
				continue
	return lines_raw


def dimdic():
	data = get_exec_cmd('sudo dmidecode -t 17 2>/dev/null')
	lines_raw = handle_result(data)
	ram_list = []
	for lines in lines_raw:
		item_ram_size = 0
		ram_item_to_dic = {}
		for i in lines:
			data = i.split(":")
			if len(data) == 2:
				key, v = data
				if key == 'Size':
					# print key ,v
					if v.strip() != "No Module Installed":
						ram_item_to_dic['size'] = v.split()[0].strip()  # e.g split "1024 MB"
						item_ram_size = int(v.split()[0])
					# print item_ram_size
					else:
						ram_item_to_dic['size'] = 0
				if key == 'Type':
					ram_item_to_dic['model'] = v.strip()
				if key == 'Manufacturer':
					ram_item_to_dic['manufactory'] = v.strip()
				if key == 'Serial Number':
					ram_item_to_dic['sn'] = v.strip()
				if key == 'Asset Tag':
					ram_item_to_dic['asset_tag'] = v.strip()
				if key == 'Locator':
					ram_item_to_dic['slot'] = v.strip()
				if key == 'Speed':
					ram_item_to_dic['speed'] = v.strip()

		if item_ram_size == 0:  # empty slot , need to report this
			pass
		else:
			ram_list.append(ram_item_to_dic)
	max_size = get_exec_cmd("sudo dmidecode|grep -P 'Maximum\s+Capacity' 2>/dev/null")
	if max_size and len(max_size[0].split(':', 1)) == 2:
		max_size = max_size[0].split(':', 1)[1].strip()
	else:
		max_size = 0
	slot_num = ("sudo dmidecode|grep -P 'Number\s+Of\s+Devices' 2>/dev/null")
	if slot_num and len(slot_num[0].split(':', 1)) == 2:
		slot_num = slot_num[0].split(':', 1)[1].strip()
	else:
		slot_num = 0
	return {
		'ansible_ram': ram_list,
		'ansible_ram_max_size': max_size,
		'ansible_ram_slot_num': slot_num
	}


def main():
	module_args = dict()
	module = AnsibleModule(
		argument_spec=module_args,
		supports_check_mode=True
	)
	if HAS_DMI:
		module.fail_json(msg='请安装相关模块 yum install dmidecode')

	ansible_facts = dimdic()
	result = dict(
		changed=False,
		ansible_facts=ansible_facts
	)
	module.exit_json(**result)


if __name__ == '__main__':
	main()
