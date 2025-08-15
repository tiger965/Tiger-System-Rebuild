# 📧 邮件通知配置说明

## ⚠️ 重要：你需要自己设置密码

我已经为你准备好了所有代码，但**你需要自己获取并设置Gmail应用专用密码**。

## 🔑 获取密码步骤

### 1. 获取Gmail应用专用密码

1. **打开浏览器，访问**: https://myaccount.google.com/
2. **登录你的账号**: a368070666@gmail.com
3. **进入安全设置**:
   - 点击左侧"安全性"
   - 找到"登录Google"部分

4. **启用两步验证**（如果还没启用）:
   - 点击"两步验证"
   - 按提示设置（通常用手机号）

5. **生成应用专用密码**:
   - 在两步验证下方，点击"应用专用密码"
   - 可能需要再次输入账户密码
   - 选择应用：选"邮件"
   - 选择设备：选"其他"，输入"Tiger系统"
   - 点击"生成"
   - **会显示一个16位密码，像这样: abcd efgh ijkl mnop**
   - ⚠️ **立即复制！只显示一次！**

### 2. 设置密码到系统

有三种方法设置密码：

#### 方法1：使用配置助手（推荐）
```bash
cd /mnt/c/Users/tiger/TigerSystem
python3 setup_email.py
# 按提示输入16位密码
```

#### 方法2：直接编辑文件
```bash
# 编辑 notification_system.py
# 找到第97行左右：
'password': '',  # 需要应用专用密码

# 改成：
'password': 'abcd efgh ijkl mnop',  # 你的16位密码
```

#### 方法3：创建密码文件
```bash
# 创建密码文件
echo '{"gmail_password": "你的16位密码"}' > config/email_password.json
chmod 600 config/email_password.json  # 设置权限
```

### 3. 测试邮件发送

```bash
# 设置密码后，运行测试
python3 test_email.py
```

如果成功，你会在 a368070666@gmail.com 收到测试邮件。

## 🤔 常见问题

### Q: 为什么不能用账户密码？
Gmail要求第三方应用使用专用密码，这样更安全。

### Q: 密码忘了怎么办？
重新生成一个新的应用专用密码。

### Q: 提示认证失败？
1. 确认使用的是16位应用专用密码
2. 确认两步验证已启用
3. 密码中的空格可以保留也可以去掉

### Q: 可以用其他邮箱吗？
可以！配置文件里有QQ邮箱、163邮箱的配置模板。

## 📝 完整流程总结

```bash
# 1. 你去Google账户获取16位密码

# 2. 运行配置助手
python3 setup_email.py
# 输入: 你的16位密码

# 3. 测试
python3 test_email.py
# 成功后会收到邮件

# 4. 使用
from notification_system import NotificationSystem
notifier = NotificationSystem()
notifier.send_alert('测试', 'HIGH', '这是测试消息')
```

## 🔒 安全提醒

- **不要**把密码提交到Git
- **不要**分享你的应用专用密码
- **建议**定期更换密码
- `.gitignore`已配置忽略密码文件

---

**记住**：我只是准备好了代码框架，实际发送邮件需要你自己的密码！