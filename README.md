## Starting the server

```
poetry run python -m computercraft.server
```


## Setting up a turtle
Then on a turtle, add the following startup program

```shell
wget http://127.0.0.1:8080/ py
```

Run `edit startup` and paste
```lua
while true do shell.run("py", "main.py"); os.sleep(2); end
```

Run `edit main.py` and paste
```
exec(open("programs/quarry.py").read())
```