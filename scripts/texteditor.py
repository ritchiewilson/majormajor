
# MajorMajor - Collaborative Document Editing Library
# Copyright (C) 2013 Ritchie Wilson
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import random
import string
import sys
import os

from gi.repository import Gtk, Pango, GObject

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))
from majormajor.majormajor import MajorMajor
from majormajor.ops.op import Op


class TextViewWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="TextView Example")

        self.set_default_size(-1, 350)

        self.grid = Gtk.Grid()
        self.add(self.grid)

        self.create_textview()
        self.create_toolbar()
        self.create_buttons()

        self.glue_majormajor()

    def glue_majormajor(self):
        
        i_id = self.textbuffer.connect('insert-text', self.insert_text_handler)
        d_id = self.textbuffer.connect('delete-range', self.delete_range_handler)
        self.majormajor_handlers = {'insert-text':i_id, 'delete-range':d_id}

        
        self.majormajor = MajorMajor()

        self.majormajor.connect('remote-cursor-update', self.remote_cursor_update)
        self.majormajor.connect('receive-changeset', self.receive_changeset)
        self.majormajor.connect('receive-snapshot', self.receive_snapshot)
        self.majormajor.connect('accept-invitation', self.accept_invitation)
        self.random_insert = False
        GObject.timeout_add(20, self.test_random_insert)

    def open_default_connection(self, listen_port):
        self.majormajor.open_default_connection(listen_port)
        self.document = self.majormajor.new_document(snapshot='')
        self.majormajor.announce()

    def open_mq_connection(self):
        self.majormajor.open_mq_connection()
        self.document = self.majormajor.new_document(snapshot='')
        self.majormajor.announce()

    def accept_invitation(self, doc):
        self.document = doc
        
    def remote_cursor_update(self):
        buf = self.textbuffer
        for i in self.majormajor.connections:
            m = buf.get_mark(i.user)
            if m != None:
                buf.delete_mark(m)
            itr = buf.get_start_iter()
            itr.set_offset(i.cursor['offset'])
            m = buf.create_mark(i.user, itr)
            m.set_visible(True)

    def insert_text_handler(s, textbuffer, iter_, text, length):
        op = Op('si', [], offset=iter_.get_offset(), val=text)
        s.document.add_local_op(op)

    def delete_range_handler(s, textbuffer, start, end):
        val = end.get_offset() - start.get_offset()
        op = Op('sd', [], offset=start.get_offset(), val=val)
        s.document.add_local_op(op)

    def receive_changeset(self, opcodes):
        h_ids = self.majormajor_handlers
        with self.textbuffer.handler_block(h_ids['insert-text']):
            with self.textbuffer.handler_block(h_ids['delete-range']):
                self.apply_opcodes(opcodes)

    def apply_opcodes(self, opcodes):
        index = 0
        for op in opcodes:
            it = self.textbuffer.get_iter_at_offset(op[2] + index)
            if op[0] == 'insert':
                self.textbuffer.insert(it, op[3])
                index += len(op[3])
            elif op[0] == 'delete':
                end = self.textbuffer.get_iter_at_offset(op[2] + op[3] + index)
                self.textbuffer.delete(it, end)
                index -= op[3]
            elif op[0] == 'replace':
                end = self.textbuffer.get_iter_at_offset(op[2] + op[3] + index)
                self.textbuffer.delete(it, end)
                it = self.textbuffer.get_iter_at_offset(op[2] + index)
                self.textbuffer.insert(it, op[4])
                index += (len(op[4]) - op[3])

    def test_random_insert(self):
        """
        When the red button is pressed, random insert toggles on and off. When
        it is on, this will pick a random, valid op to add to the document.
        This will get called repeatedly on a timer to quickly fill the text
        buffer with gibberish and see if collaboration can keep up.
        """
        if not self.random_insert:
            return True
        doc = self.document
        old_state = doc.get_snapshot()
        n = random.randint(1, 5)
        o = random.randint(0, len(doc.get_snapshot()))
        if random.random() > .3 or len(doc.get_snapshot()) == 0:
            letters = [random.choice(string.ascii_letters + string.digits)
                       for x in range(n)]
            l = unicode(''.join(letters))
            doc.add_local_op(Op('si', [], offset=o, val=l))
        else:
            while o + n > len(doc.get_snapshot()):
                n -= 1
            if o == len(doc.get_snapshot()):
                o -= 1
                n = 1
            doc.add_local_op(Op('sd', [], offset=0, val=n))
        doc.close_changeset()
        opcodes = doc.get_diff_opcode(old_state)
        self.receive_changeset(opcodes)
        return True

    def receive_snapshot(self, snapshot):
        h_ids = self.majormajor_handlers
        with self.textbuffer.handler_block(h_ids['insert-text']):
            with self.textbuffer.handler_block(h_ids['delete-range']):
                self.textbuffer.set_text(snapshot)

    def create_toolbar(self):
        toolbar = Gtk.Toolbar()
        self.grid.attach(toolbar, 0, 0, 3, 1)

        button_save = Gtk.ToolButton.new_from_stock(Gtk.STOCK_SAVE)
        toolbar.insert(button_save, 0)

        button_random = Gtk.ToggleToolButton(Gtk.STOCK_MEDIA_RECORD)
        toolbar.insert(button_random, 1)

        button_drop_css = Gtk.ToggleToolButton(Gtk.STOCK_CANCEL)
        toolbar.insert(button_drop_css, 2)

        button_invite = Gtk.ToolButton()
        button_invite.set_stock_id(Gtk.STOCK_YES)
        toolbar.insert(button_invite, 3)

        button_save.connect("clicked", self.on_save_clicked)
        button_random.connect("clicked", self.on_random_clicked)
        button_drop_css.connect("clicked", self.on_drop_css_clicked)
        button_invite.connect("clicked", self.on_invite_clicked)



    def create_textview(self):
        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        self.grid.attach(scrolledwindow, 0, 1, 3, 1)

        self.textview = Gtk.TextView()
        self.textbuffer = self.textview.get_buffer()
        scrolledwindow.add(self.textview)

        self.textview.set_wrap_mode(True)

        self.tag_bold = self.textbuffer.create_tag("bold",
            weight=Pango.Weight.BOLD)
        self.tag_italic = self.textbuffer.create_tag("italic",
            style=Pango.Style.ITALIC)
        self.tag_underline = self.textbuffer.create_tag("underline",
            underline=Pango.Underline.SINGLE)
        self.tag_found = self.textbuffer.create_tag("found",
            background="yellow")

    def create_buttons(self):
        check_editable = Gtk.CheckButton("Editable")
        check_editable.set_active(True)
        check_editable.connect("toggled", self.on_editable_toggled)
        self.grid.attach(check_editable, 0, 2, 1, 1)

        check_cursor = Gtk.CheckButton("Cursor Visible")
        check_cursor.set_active(True)
        check_editable.connect("toggled", self.on_cursor_toggled)
        self.grid.attach_next_to(check_cursor, check_editable,
            Gtk.PositionType.RIGHT, 1, 1)

        radio_wrapnone = Gtk.RadioButton.new_with_label_from_widget(None,
            "No Wrapping")
        self.grid.attach(radio_wrapnone, 0, 3, 1, 1)

        radio_wrapchar = Gtk.RadioButton.new_with_label_from_widget(
            radio_wrapnone, "Character Wrapping")
        self.grid.attach_next_to(radio_wrapchar, radio_wrapnone,
            Gtk.PositionType.RIGHT, 1, 1)

        radio_wrapword = Gtk.RadioButton.new_with_label_from_widget(
            radio_wrapnone, "Word Wrapping")
        self.grid.attach_next_to(radio_wrapword, radio_wrapchar,
            Gtk.PositionType.RIGHT, 1, 1)

        radio_wrapnone.connect("toggled", self.on_wrap_toggled, Gtk.WrapMode.NONE)
        radio_wrapchar.connect("toggled", self.on_wrap_toggled, Gtk.WrapMode.CHAR)
        radio_wrapword.connect("toggled", self.on_wrap_toggled, Gtk.WrapMode.WORD)

    def on_save_clicked(self, widget):
        #self.document.ot()
        #self.document.rebuild_snapshot()
        import random
        n = "".join([random.choice("abcdef") for x in range(3)])
        n = "buffer-" + n + ".txt"
        f = open(n, 'w')
        #start = self.textbuffer.get_start_iter()
        #end = self.textbuffer.get_end_iter()
        #f.write(self.textbuffer.get_text(start, end,True))
        f.write(self.document.get_snapshot())
        ol = self.document.get_ordered_changesets()
        for cs in ol:
            f.write("\nCS ID: "+cs.get_id()[:8]+'\n')
            p_ids = [parent.get_id() for parent in cs.get_parents()]
            p_ids.sort()
            f.write("  PARETNS, "+", ".join(p_ids))
            f.write("\nOPS")
            for op in cs.get_ops():
                f.write("     TOffset " + str(op.t_offset))
                f.write("     Offset " + str(op.offset))
                f.write("     TVal "+str(op.t_val))
                f.write("     Val "+str(op.val))
                f.write("\n")
            f.write("\n")
            for ucs in cs.get_unaccounted_changesets():
                f.write("    " + ucs.get_id()[:8])
                #if ucs.user == self.majormajor.default_user:
                #    f.write("  <---- local")
                f.write("\n")
        f.close()

    def on_random_clicked(self, widget):
        self.random_insert = not self.random_insert

    def on_drop_css_clicked(self, widget):
        b = self.majormajor.drop_random_css
        self.majormajor.drop_random_css = not b

    def on_invite_clicked(self, widget):
        self.majormajor.invite_all(self.document)

    def on_button_clicked(self, widget, tag):
        self.majormajor.big_insert = not self.majormajor.big_insert

        bounds = self.textbuffer.get_selection_bounds()
        if len(bounds) != 0:
            start, end = bounds
            self.textbuffer.apply_tag(tag, start, end)

    def on_clear_clicked(self, widget):
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.remove_all_tags(start, end)

    def on_editable_toggled(self, widget):
        self.textview.set_editable(widget.get_active())

    def on_cursor_toggled(self, widget):
        self.textview.set_cursor_visible(widget.get_active())

    def on_wrap_toggled(self, widget, mode):
        self.majormajor.big_insert = not self.majormajor.big_insert
        self.textview.set_wrap_mode(mode)

    def on_justify_toggled(self, widget, justification):
        self.textview.set_justification(justification)


import argparse

parser = argparse.ArgumentParser(description='Demo collaborative text editor.')
parser.add_argument('-port', type=int)
parser.add_argument('-mq', action='store_const', const=1)
args = parser.parse_args()

win = TextViewWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()
if args.port or (not args.port and not args.mq):
    port = args.port if args.port else 8000
    win.open_default_connection(port)
elif args.mq:
    win.open_mq_connection()

Gtk.main()
            
    
