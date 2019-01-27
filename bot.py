from decensor import Decensor

import discord
from discord.ext import commands
import os

from queue import Queue

from threading import Thread

import io
from io import BytesIO
import requests
from PIL import Image

import asyncio

bot = commands.Bot(command_prefix='.')
bot.remove_command('help')

REACT_CONFIRM = u"\u2705"
REACT_THINK = u"\U0001F4AD"
REACT_IGNORE = u"\u274C"

OUTPUT_EXTENSION = '_d'
OUTPUT_TYPE = 'PNG'

class DecensorJob:
	def __init__(self, image, ctx, file_name, file_extension):
		self.image = image
		self.ctx = ctx
		self.file_name = file_name
		self.file_extension = file_extension

decensor_input = Queue()
decensor_output = Queue()

@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)
	print('------')

@bot.command(pass_context=True,)
async def rm(ctx):
	# Vars
	if (len(ctx.message.attachments) == 0):
		print("No attachment found. Ignored.")
		await bot.add_reaction(ctx.message, REACT_IGNORE)
		return
	
	attachment = ctx.message.attachments[0]
	file_name, file_extension = os.path.splitext(attachment['filename'])
	
	# Download pic
	try:
		url = attachment['url']
		data = requests.get(url).content
		img = Image.open(io.BytesIO(data))
	except OSError:
		print("Invalid image type. Ignored.")
		await bot.add_reaction(ctx.message, REACT_IGNORE)
		return
	
	decensor_input.put(DecensorJob(img, ctx, file_name, file_extension))
	print('Added', file_name, 'to the queue')
	await bot.add_reaction(ctx.message, REACT_THINK)

# Syncronous
def decensor_worker():
	print('Loading DeepCreamPy')
	dcp = Decensor()
	while not bot.is_closed:
		next = decensor_input.get()
		print('Attemping to decensor', next.file_name)
		
		next.image = dcp.decensor_image(next.image, next.image)
		
		decensor_output.put(next);

async def decensor_outputter():
	await bot.wait_until_ready()
	while not bot.is_closed:
		try:
			next = decensor_output.get(True, 1)
			print('Sending', next.file_name + OUTPUT_EXTENSION)
			modifed_name = next.file_name + OUTPUT_EXTENSION + "." + OUTPUT_TYPE
			
			# convert pillow Image to file-like byte stream
			b = io.BytesIO()
			next.image.save(b, OUTPUT_TYPE)
			b.seek(0)
			
			await bot.send_file(next.ctx.message.channel, b, filename=modifed_name)
			print('Done.')
		except:
			pass
		await asyncio.sleep(1)

# Because this handler needs to be an async task for discord.py to send messages.
bot.loop.create_task(decensor_outputter())

# Because if you hang discord.py with a long task it
# crashes from not being able to ping discord servers.
thread = Thread(target = decensor_worker)
thread.daemon = True
thread.start();

# Pasting your token in source sucks. Lets keep it seperate from the code.
try:
	# Get token from file
	f = open('token')
	token = f.readline()
	f.close()
except:
	# No token saved. Ask for the token and use it
	token = input("Enter your token for the bot: ").strip()
	with open('token', 'a') as f:
		f.write(token)

try:
	bot.run(token)
except discord.errors.LoginFailure:
	print('Invalid token.')
	try:
		os.remove('token')
	except OSError:
		pass
	exit(1)