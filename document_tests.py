from document import Document
import unittest


class TestSimpleNodeOperations(unittest.TestCase):

    def setUp(self):
        self.doc = Document()
        self.doc.content = {'first': 'some string',
                            'second': {'third':'more string',
                                       'fourth':{'numb':55}},
                            'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}

    def test_insert_pair(self):
        self.doc.content = {}
        d1 = {'key': 'first',
              'value': 'some string',
              'node': ''}
        result1 = {'first': 'some string'}

        d2 = {'key': 'second',
              'value': {},
              'node': ''}
        result2 = {'first': 'some string', 'second':{}}

        d3 = {'key': 'third',
              'value': 'more string',
              'node': 'second'}
        result3 = {'first': 'some string', 'second':{'third':'more string'}}

        self.doc.insert_pair(d1)
        self.assertEqual(self.doc.content, result1)
        self.doc.insert_pair(d2)
        self.assertEqual(self.doc.content, result2)
        self.doc.insert_pair(d3)
        self.assertEqual(self.doc.content, result3)

    def test_remove_pair(self):
        c1 = {'node': '', 'key':'first'}
        result1 = {'second': {'third':'more string',
                              'fourth':{'numb':55}},
                    'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}

        c2 = {'node': 'second,fourth', 'key':'numb'}
        result2 = {'second': {'third':'more string',
                              'fourth':{}},
                    'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}

        self.doc.remove_pair(c1)
        self.assertEqual(self.doc.content, result1)
        self.doc.remove_pair(c2)
        self.assertEqual(self.doc.content, result2)

    def test_find_node(self):
        pos1 = ''
        pos2 = 'first'
        pos3 = 'second'
        pos4 = 'second,third'
        pos5 = 'fifth,1'
        pos6 = 'fifth,2,sixth'
        pos7 = 'fifth,3'

        self.assertEqual(self.doc.find_node(pos1), self.doc.content)
        self.assertEqual(self.doc.find_node(pos2),'some string')
        self.assertEqual(self.doc.find_node(pos3),
                         {'third':'more string',
                         'fourth':{'numb':55}})
        self.assertEqual(self.doc.find_node(pos4), 'more string')
        self.assertEqual(self.doc.find_node(pos5), 66)
        self.assertEqual(self.doc.find_node(pos6), 'deep string')
        self.assertEqual(self.doc.find_node(pos7), 'rw')

    def test_insert_into_array(self):
        d1 = {'value':44,
              'pos':0,
              'node':'fifth'}
        result1 = {'first': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                              'fifth':[44,55,66,{'sixth': 'deep string'}, 'rw']}

        d2 = {'value':{'inserted':'node'},
              'pos':4,
              'node':'fifth'}
        result2 = {'first': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                    'fifth':[44,55,66,
                             {'sixth': 'deep string'},
                             {'inserted': 'node'}, 'rw']}

        self.doc.insert_into_array(d1)
        self.assertEqual(self.doc.content, result1)
        self.doc.insert_into_array(d2)
        self.assertEqual(self.doc.content, result2)

    def test_remove_from_array(self):
        c1 = {'pos':2, 'node':'fifth'}
        result1 = {'first': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                    'fifth': [55,66,'rw']}

        c2 = {'pos':2, 'node':'fifth'}
        result2 = {'first': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                    'fifth': [55,66]}

        c3 = {'pos':0, 'node':'fifth'}
        result3 = {'first': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                    'fifth': [66]}
        c4 = {'pos':0, 'node':'fifth'}
        result4 = {'first': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                    'fifth': []}

        self.doc.remove_from_array(c1)
        self.assertEqual(self.doc.content, result1)
        self.doc.remove_from_array(c2)
        self.assertEqual(self.doc.content, result2)
        self.doc.remove_from_array(c3)
        self.assertEqual(self.doc.content, result3)
        self.doc.remove_from_array(c4)
        self.assertEqual(self.doc.content, result4)

    def test_change_key(self):
        c1 = {'node': '', 'key':'first', 'new_key':'changed_key_here'}
        result1 = {'changed_key_here': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                   'fifth': [55,66,{'sixth': 'deep string'}, 'rw']}

        c2 = {'node': 'fifth,2', 'key':'sixth', 'new_key':'seventh'}
        result2 = {'changed_key_here': 'some string',
                   'second': {'third':'more string',
                              'fourth':{'numb':55}},
                   'fifth': [55,66,{'seventh': 'deep string'}, 'rw']}

        self.doc.change_key(c1)
        self.assertEqual(self.doc.content, result1)
        self.doc.change_key(c2)
        self.assertEqual(self.doc.content, result2)

if __name__ == '__main__':
    unittest.main()
