## Starting the server

```
poetry run python -m computercraft.server
```


## Setting up a turtle
Then on a turtle, add the following startup program

```shell
wget http://127.0.0.1:8080/ py
```

Write in `startup`
```lua
shell.run("py", "main.py")
```

Write in `main.py`
```
exec(open("programs/quarry.py").read())
```

# Attributions
## simpleAStar
The astar implementation is a modified version of fvilmos 
astar implementation, which can be found [here](https://github.com/fvilmos/simpleAstar).