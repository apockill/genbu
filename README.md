# Genbu
Genbu is the Japenese name for Black Tortoise, a symbol of a turtle and a snake. 

## Introduction
This project combines ComputerCraft turtles, 
a [project to control them via python](https://github.com/neumond/python-computer-craft), 
with a large set of built-in utilities. 

Using this project, you can kickstart your turtle project with built-in pathfinding, robust stateless programming patterns, and the ability to survive chunkloading, save reloading, and other things that normally interrupt turtle tasks. 

## Getting Started
### Install Dependencies
```
poetry install
```
### Start the server

```
poetry run python -m computercraft.server
```


### Set up a turtle
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

Tada! You are now running the `quarry.py` program on your turtle.
