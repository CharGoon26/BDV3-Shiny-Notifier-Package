# Shiny Notifier Package

BallsDex package that allows bot admins to assign a channel that posts notifications whenever a player catches a `Shiny` special card on any server. 

## What it does

- Detects catches whose special name matches `Shiny` by default. This will not work if your event is not exactly called 'Shiny'
- Sends a message to one configured Discord channel
- Provides bot-admin-only slash commands to manage the channel and check status

## Install

Add the package to your `config/extra.toml`:

```toml
[[ballsdex.packages]]
location = "git+https://github.com/CharGoon26/BDV3-Shiny-Notifier-Package"
path = "shiny_notifier"
enabled = true  
```

Then `docker compose build --no-cache` then `docker compose restart bot`

## Commands

- `/shiny notifier channel` — set the notification channel
- `/shiny notifier status` — view the current setup

These commands are intended for bot staff only. Regular users may see the command name, but they cannot use it.

## Possible side effects

- If the configured channel is deleted or becomes inaccessible, notifications will stop until the channel is updated again

