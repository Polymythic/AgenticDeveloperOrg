# 🚀 Slack Integration Setup Checklist

**Status**: ✅ Ready for Live Configuration  
**Phase**: 3 - Requirements Intake & Communication  
**Last Updated**: 2025-07-05

---

## 📋 Quick Setup Checklist

### 1. **Environment Configuration** ⚙️
- [ ] Copy `env.example` to `.env` (if not already done)
- [ ] Set `SLACK_ENABLED=true`
- [ ] Add your `SLACK_BOT_TOKEN` (starts with `xoxb-`)
- [ ] Configure `SLACK_CHANNELS` (comma-separated list)
- [ ] (Optional) Add `SLACK_WEBHOOK_URL` for incoming webhooks
- [ ] (Optional) Add `SLACK_APP_TOKEN` for socket mode

### 2. **Slack App Creation** 🤖
- [ ] Go to https://api.slack.com/apps
- [ ] Click "Create New App" → "From scratch"
- [ ] Name: "Agentic Developer System" (or your preferred name)
- [ ] Select your workspace

### 3. **Bot Token Scopes** 🔐
- [ ] Go to "OAuth & Permissions"
- [ ] Add these Bot Token Scopes:
  - [ ] `chat:write` (send messages)
  - [ ] `channels:read` (list channels)
  - [ ] `channels:history` (read messages)
  - [ ] `files:read` (read uploaded files)
  - [ ] `app_mentions:read` (respond to mentions)
  - [ ] `users:read` (get user info)

### 4. **Install App** 📦
- [ ] Go to "OAuth & Permissions"
- [ ] Click "Install to Workspace"
- [ ] Copy the "Bot User OAuth Token" (starts with `xoxb-`)
- [ ] Add this token to your `.env` file

### 5. **Event Subscriptions (Optional)** 🔄
- [ ] Go to "Event Subscriptions"
- [ ] Enable Events
- [ ] Set Request URL to: `https://your-domain.com/integrations/slack/webhook`
- [ ] Subscribe to these events:
  - [ ] `message.channels` (receive messages)
  - [ ] `app_mention` (respond to mentions)
  - [ ] `file_shared` (process uploaded files)

### 6. **Test Integration** 🧪
- [ ] Restart your application: `python start.py`
- [ ] Run test suite: `python test_slack_integration.py`
- [ ] Check all tests pass (should be 100% success rate)
- [ ] Verify test messages appear in your Slack channels

---

## 🔧 Configuration Examples

### Basic Configuration (.env)
```bash
# Enable Slack integration
SLACK_ENABLED=true

# Your bot token (get from Slack App OAuth & Permissions)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# Channels to monitor/send to (comma-separated)
SLACK_CHANNELS=general,code-reviews,agent-requests

# Optional: Webhook URL for incoming events
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Optional: App token for socket mode
SLACK_APP_TOKEN=xapp-your-app-token-here
```

### Channel Configuration Options
```bash
# By name (easier to read)
SLACK_CHANNELS=general,code-reviews,security-alerts

# By ID (more reliable)
SLACK_CHANNELS=C1234567890,C0987654321,C1112223333

# Mixed (both names and IDs)
SLACK_CHANNELS=general,C1234567890,code-reviews
```

---

## 🧪 Testing Commands

### Test Slack Integration
```bash
python test_slack_integration.py
```

### Test API Endpoints
```bash
# Check Slack status
curl http://localhost:8000/integrations/slack/status

# Test connection
curl -X POST http://localhost:8000/integrations/slack/test

# Send test message
curl -X POST "http://localhost:8000/integrations/slack/send" \
  -H "Content-Type: application/json" \
  -d '{"channel": "general", "message": "🧪 Test message from API"}'

# List channels
curl http://localhost:8000/integrations/slack/channels
```

---

## 🎯 Usage Examples

### Requirements Intake
Users can now:
- **Send messages** like "Create a login form" → routes to `agentic_software_developer`
- **Upload screenshots** → automatically analyzed for requirements
- **Upload documents** → parsed for specifications
- **Mention the bot** → `@your-bot create a dashboard` → direct agent routing

### Agent Responses
- **Rich formatting** with blocks and metadata
- **Thread support** for organized conversations
- **Automatic routing** based on keywords
- **File processing** for screenshots and documents

---

## 🚨 Troubleshooting

### Common Issues
1. **"Slack integration is disabled"**
   - Check `SLACK_ENABLED=true` in `.env`
   - Restart the application

2. **"Authentication failed"**
   - Verify bot token starts with `xoxb-`
   - Check token hasn't expired
   - Ensure app is installed to workspace

3. **"Channel not found"**
   - Verify channel names/IDs in `SLACK_CHANNELS`
   - Ensure bot is invited to channels
   - Check bot has `channels:read` scope

4. **"Cannot send messages"**
   - Check bot has `chat:write` scope
   - Verify bot is in the target channel
   - Check channel permissions

### Debug Commands
```bash
# Check configuration
curl http://localhost:8000/config | jq '.integrations.slack'

# Test connection with details
curl -X POST http://localhost:8000/integrations/slack/test | jq '.'

# Check health
curl http://localhost:8000/health | jq '.integrations'
```

---

## 📚 Next Steps

After Slack is configured:
1. **Test requirements intake** by sending messages and uploading files
2. **Verify agent responses** appear in Slack with proper formatting
3. **Set up webhooks** for real-time event processing
4. **Configure GitHub integration** (Phase 4) for complete workflow
5. **Monitor logs** for any issues or improvements

---

**🎉 You're ready to enable live Slack integration!** 