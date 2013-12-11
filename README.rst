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

Try the sample text editor in the scripts directory::

    $ python texteditor.py


Then in a separate terminal, open another instance of the text editor. Open 
as many as you like.

In any texteditor window, the green checkmark button will invite the others
to work on the same document and keep in sync. The red "X" will take that
editor offline. Bring it back online and watch the documents sync up.


Tests
-----

The tests are done with pytest. From the project root, run ``py.test``.


License
-------

GPLv3 or later


Contact
-------

MajorMajor was created by Ritchie Wilson, wilson.ri@husky.neu.edu

More info found at http://www.majormajor.org

