
MajorMajor
==========

MajorMajor is a library for handling peer-to-peer, real-time,
collaborative document editing. It is meant to be used as a plugin for
existing desktop applications, giving them the ability to be used
collaboratively over a network. MajorMajor requires no central
server. Users just send messages to each other over whatever protocol
they choose, and MajorMajor is responsible for keeping the group in
sync.

Quick Start
-----------

Checkout the code over ssh:
`git clone git@majormajor.org:repos/majormajor.git`

or over http:
`git clone http://git.majormajor.org:/majormajor.git`


Sample Text Editor
------------------

Try the sample text editor in the scripts directory:
```
$ python texteditor.py
```

Then in a separate terminal, open another instance of the text editor:
```
$ python texteditor.py
```

Open as many as you like.

In any texteditor window, the green checkmark button will invite the others
to work on the same document and keep in sync.


Tests
-----

The tests are done with pytest. From the project root, run `py.test`.

Goals vs. Status
----------------

MajorMajor minimally works, but is not nearly complete.

 - **Full JSON Support** -- MajorMajor currently only handles plain
     text, but is designed to eventually handle any json document.
 - **Easy Integration** -- With some glue, MajorMajor should be easily
     plugged into existing desktop programs. Currently it is hard
     coded to work with some GObject based examples.
 - **Arbitrary Network Protocols** -- Messages between users are
     currently UDP packets broadcast over a local network. However the
     Connection module is extensible, and should handle anything
     (http, IRC, XMPP, TorChat)

License
-------

GPLv3 or later


Contact
-------

MajorMajor was created by Ritchie Wilson, wilson.ri@husky.neu.edu

All info found at http://www.majormajor.org

