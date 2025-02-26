
import json
import os
import instaloader
from datetime import datetime, timedelta
import asyncio
import discord
from typing import Dict, List, Optional

class InstagramManager:
    def __init__(self, bot):
        self.bot = bot
        self.accounts_file = "instagram_accounts.json"
        self.accounts: Dict[str, List[int]] = {}
        self.loader = instaloader.Instaloader()
        self.last_check = {}
        self.load_accounts()

    def load_accounts(self):
        try:
            if os.path.exists(self.accounts_file):
                with open(self.accounts_file, 'r') as f:
                    self.accounts = json.load(f)
                    for username in self.accounts:
                        self.last_check[username] = datetime.now() - timedelta(hours=24)
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.accounts = {}

    def save_accounts(self):
        try:
            with open(self.accounts_file, 'w') as f:
                json.dump(self.accounts, f)
        except Exception as e:
            print(f"Error saving accounts: {e}")

    async def add_account(self, username: str, channel_id: int) -> bool:
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            if username not in self.accounts:
                self.accounts[username] = []
            if channel_id not in self.accounts[username]:
                self.accounts[username].append(channel_id)
            self.last_check[username] = datetime.now() - timedelta(hours=24)
            self.save_accounts()
            return True
        except Exception as e:
            print(f"Error adding account: {e}")
            return False

    async def remove_account(self, username: str, channel_id: int) -> bool:
        try:
            if username in self.accounts:
                if channel_id in self.accounts[username]:
                    self.accounts[username].remove(channel_id)
                    if not self.accounts[username]:
                        del self.accounts[username]
                    self.save_accounts()
                    return True
            return False
        except Exception as e:
            print(f"Error removing account: {e}")
            return False

    async def check_updates(self, username: str) -> List[dict]:
        updates = []
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            # Check posts
            for post in profile.get_posts():
                if post.date > self.last_check[username]:
                    updates.append({
                        'type': 'post',
                        'url': f"https://www.instagram.com/p/{post.shortcode}/",
                        'caption': post.caption if post.caption else "No caption",
                        'timestamp': post.date
                    })

            # Check stories
            try:
                for story in profile.get_stories():
                    if story.date > self.last_check[username]:
                        updates.append({
                            'type': 'story',
                            'url': story.url,
                            'timestamp': story.date
                        })
            except Exception:
                pass  # Stories might be private or unavailable

            self.last_check[username] = datetime.now()
            return updates
        except Exception as e:
            print(f"Error checking updates for {username}: {e}")
            return []

    async def send_update(self, channel_id: int, username: str, update: dict):
        try:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title=f"New Instagram {update['type']} from @{username}",
                    description=update.get('caption', ''),
                    url=update['url'],
                    color=0xE1306C,
                    timestamp=update['timestamp']
                )
                embed.set_footer(text=f"Instagram {update['type']}")
                await channel.send(embed=embed)
        except Exception as e:
            print(f"Error sending update: {e}")

    async def check_all_accounts(self):
        for username, channels in self.accounts.items():
            updates = await self.check_updates(username)
            for update in updates:
                for channel_id in channels:
                    await self.send_update(channel_id, username, update)
