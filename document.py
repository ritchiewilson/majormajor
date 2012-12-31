import unittest
import json

class Document:
    content = {}
    change_history = []
    revision = 0

    def find_node(self, pos):
        node = self.content

        traverse = pos.split(',')

        for i in traverse:
            if i!='':
                try:
                    index = int(i)
                    node = node[index]
                except ValueError:
                    node = node[i]
        return node


    def modify(self, changeset, from_revision):
        op = changeset.op
        if op == 'insert_pair':
            self.insert_pair(changeset)
        elif op == 'remove_pair':
            self.remove_pair(changeset)
        elif op == 'insert_into_array':
            self.insert_into_array(changeset)
        elif op == 'insert_into_array':
            self.insert_into_array(changeset)
        elif op == 'insert_into_array':
            self.insert_into_array(changeset)

    def add_to_change_history(self, op, args):
        change = args
        change['op'] = op
        self.change_history.append(change)
        self.revision += 1

    def insert_pair(self, change):
        key = change['key']
        value = change['value']
        node = self.find_node(change['node'])
        node[key] = value
        self.add_to_change_history('insert_pair', change)

    def remove_pair(self, change):
        key = change['key']
        node = self.find_node(change['node'])
        del node[key]
        self.add_to_change_history('remove_pair', change)

    def insert_into_array(self, change):
        value = change['value']
        pos = change['pos']
        node = self.find_node(change['node'])
        node.insert(pos,value)
        self.add_to_change_history('insert_into_array', change)

    def remove_from_array(self, change):
        pos = change['pos']
        node = self.find_node(change['node'])
        node.pop(pos)
        self.add_to_change_history('remove_from_array', change)

    def change_key(self, change):
        key = change['key']
        node = self.find_node(change['node'])
        new_key = change['new_key']
        node[new_key] = node[key]
        del node[key]
        self.add_to_change_history('change_key', change)
