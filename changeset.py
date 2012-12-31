class Changeset:
    def __init__(self, op, rev, synced_rev, path=[], pos='', value=None):
        self.op_raw = op
        self.op = op
        self.rev_raw = rev
        self.rev = rev
        self.synced_rev = synced_rev
        self.value_raw = value
        self.value = value

        # pos is the position of whatever is being modified. If an
        # object is being modified, this is a string for the key. If
        # an array is being modified, an int for it's index. If
        # string, then the position of the text being modified. For
        # number, bool, or null, the position does not matter and
        # defaults to zero.  key, int if array
        self.pos_raw = pos
        self.pos = pos

        if type(path)==list:
            self.path = path
        else:
            self.parse_path(path)

    def parse_path(self, path):
        self.path = []
        traverse = path.split(',')
        for i in traverse:
            if i!='':
                try:
                    index = int(i)
                    self.path.append(index)
                except ValueError:
                    self.path.append(i)
        return self.path

    def merge_past_changeset(self, past_revision):
        op = past_revision.op
        if op == 'insert_pair':
            self.merge_in_insert_pair(past_revision)
        elif op == 'remove_pair':
            self.merge_in_remove_pair(past_revision)
        elif op == 'insert_into_array':
            self.merge_in_insert_into_array(past_revision)

    def merge_in_insert_pair(self, past_revision):
        self.rev = past_revision.rev + 1
        # For when this changeset is an insert_pair, and some past
        # revisions need to be merged in.

    def merge_in_remove_pair(self, past_revision):
        # whenever the previous revision has removed the node this
        # change operates on, just negate this opperation
        removed_node = past_revision.path
        removed_node.append(past_revision.pos)
        if removed_node == self.path[0:len(removed_node)]:
            self.op = None


    def merge_in_insert_into_array(self, past_revision):
        # a past revision of insert_into_array can only affect this
        # changeset by changing its path
        if past_revision.path == self.path[0:len(past_revision.path)]:
            if past_revision.pos <= self.path[len(past_revision.path)]:
                self.path[len(past_revision.path)] += 1
        #TODO: There is an edge case of merging insert_into_array into
        #insert_into_array, and need to figure out which should
        #actually be considered to be first.
