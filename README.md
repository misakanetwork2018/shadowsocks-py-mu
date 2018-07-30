About Shadowsocks-python Manyuser
=================================
This is a multi-user version of shadowsocks-python. Requires a mysql database or a panel which supports SS MU API.

Requirement
-----------
1. Python >= 2.5 (python=2.5 need to install extra library: `pip install simplejson`)
2. MySQL >= 5 (if using database)
3. A Panel with [MU API](https://github.com/fsgmhoward/shadowsocks-py-mu/wiki/MultiUser-(MU)-API-Reference), such as [SS-Panel V3](https://github.com/orvice/ss-panel). (if using MU API)

Install Instructions for Database User
--------------------------------------
1. install `cymysql` library by `pip install cymysql`
2. create a database named `shadowsocks`
3. import `shadowsocks.sql` into the `shadowsocks` database
4. copy `config_example.py` to `config.py` and edit it following the notes inside (but DO NOT delete the example file). You *DO NOT* need to edit the API section.
5. TestRun `cd shadowsocks && python servers.py` (not server.py)

Install Instructions for MU API User
-----------------------------------
1. copy `config_example.py` to `config.py` and edit it following the notes inside (but DO NOT delete the example file). You *DO NOT* need to edit the Database section.
2. TestRun `cd shadowsocks && python servers.py` (not server.py)

Install Instructions for Docker User
------------------------------------

1. build the docker: `docker build -t shadowsocks-mu .`
2. create a config file as above
3. run the docker (random free ports will be allocated):

   ```
   docker run -it \
       -v /PATH/TO/CONFIG/FILE:/shadowsocks/shadowsocks/config.py \
       -v /PATH/TO/LOG/FILE:/shadowsocks/shadowsocks/shadowsocks.log \
       -p PORT_START-PORT_END \
       shadowsocks-mu
   ```
   
   If you want to use fixed ports (e.g. port 443 of the host being matched with 443 of the docker), use `-p PORT_START-PORT_END:PORT_START-PORT_END` instead.
   
   Note: `/PATH/TO/CONFIG/FILE` & `/PATH/TO/LOG/FILE` should be **absolute** paths

Reminders for Windows User
--------------------------
1. install `pyuv` library by `pip install pyuv`
2. if git is not configured in your `%PATH%` environmental variable, you can create a file named `.nogit` to avoid using `git describe`

If no exceptions are thrown, the server will startup. By default, logging is enabled.
You should be able to see this kind of thing in `shadowsocks.log`(default log file name)
```
Jun 24 01:06:08 INFO -----------------------------------------
Jun 24 01:06:08 INFO Multi-User Shadowsocks Server Starting...
Jun 24 01:06:08 INFO Current Server Version: 3.1.0-1-gc2ac618

Jun 24 01:10:11 INFO api downloaded
Jun 24 01:10:13 INFO api skipped port 443
Jun 24 01:10:13 INFO Server Added:   P[XXXXX], M[rc4-md5], E[XXXXX@gmail.com]
Jun 24 01:10:13 INFO Server Added:   P[XXXXX], M[rc4-md5], E[XXXXX@gmail.com]
```

Explanation of the log output
-----------------------------
When adding server:

`P[XXX]` client port (assigned by database)

`M[XXX]` client encryption method

`E[XXX]` client email address

When data connection being established/blocked

`U[XXX]` client port (assigned by database)

`RP[XXX]` remote port (the port the client wants to connect)

`A[XXX-->XXX]` from the client address to the remote address

Database user table column
--------------------------
`passwd` server pass

`port` server port

`t` last connecting time

`u` no usage for this shadowsocks server (kept unchanged) but essential for some panels

`d` accumulated upload + download data transfer

`method` custom encryption method

`enable`/`switch` indicating whether the user is enabled

`transfer_enable` maximum accumulated data transfer allowed - if `u` + `d` > `transfer_enable`, service for this client will be stopped (other clients are not affected)

Compatibility with frontend UIs
-------------------------------
It is fully compatible (through [MU API](https://github.com/fsgmhoward/shadowsocks-py-mu/wiki/MultiUser-(MU)-API-Reference)) with [ss-panel V3](https://github.com/orvice/ss-panel) .

Open source license
-------------------
This program is licensed under [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0)
