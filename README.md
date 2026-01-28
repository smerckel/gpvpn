write something about adding group gpvpn and that a user should be in
it.


```
sudo useradd gpvpn
```

```
sudo usermod -aG gpvpn <your login name>
```

logout and login


gpauth --fix-openssl --default-browser --gateway gpp.hereon.de | sudo
gpclient --fix-openssl connect --cookie-on-stdin --as-gateway
gpp.hereon.de 

See also issue #572 of the github page
