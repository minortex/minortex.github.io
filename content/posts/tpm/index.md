+++
date = '2026-05-05T16:49:51+08:00'
draft = false
title = '简单了解和手动使用 TPM'
tags = ['Linux', 'Arch Linux']
+++


最近疯狂迷恋 tpm，这个小玩意究竟是怎么实现基于设备的安全的？

## tpm 的相关属性

第一步，我们先看下 tpm 有什么变量是可以被改变的：

```bash
sudo tpm2_getcap properties-variable
```

### 第一组：永久属性组 (PT -> Property)

```bash
TPM2_PT_PERMANENT:
  ownerAuthSet:              0 # 所有者鉴权密码
  endorsementAuthSet:        0 # 背书鉴权密码
  lockoutAuthSet:            0 # 锁定鉴权密码
  reserved1:                 0
  disableClear:              0
  inLockout:                 0
  tpmGeneratedEPS:           1
  reserved2:                 0
```

### 第二组：启动时状态

```bash
TPM2_PT_STARTUP_CLEAR:
  phEnable:                  1 # 平台层级，也就是你可以在系统里面清除tpm所有信息
  shEnable:                  1 # 存储层级，其实跟owner是一样的
  ehEnable:                  1 # 背书层级
  phEnableNV:                1
  reserved1:                 0
  orderly:                   1 
```

### 第三组：句柄资源 (HR -> Handle Resource)

```bash
TPM2_PT_HR_NV_INDEX: 0x5
TPM2_PT_HR_LOADED: 0x0 # 当前已加载密钥
TPM2_PT_HR_LOADED_AVAIL: 0x3 
TPM2_PT_HR_ACTIVE: 0x0 # 已激活的会话
TPM2_PT_HR_ACTIVE_AVAIL: 0x40 
TPM2_PT_HR_TRANSIENT_AVAIL: 0x3 # 临时会话，从存储读入内存
TPM2_PT_HR_PERSISTENT: 0x0 # 可以永久存储的槽位
TPM2_PT_HR_PERSISTENT_AVAIL: 0x2
```

### 第四组：锁定相关配置

```bash
TPM2_PT_LOCKOUT_COUNTER: 0x0
TPM2_PT_MAX_AUTH_FAIL: 0xC8
TPM2_PT_LOCKOUT_INTERVAL: 0x0
TPM2_PT_LOCKOUT_RECOVERY: 0x0
```

### 第五组：杂项

```bash
TPM2_PT_NV_COUNTERS: 0x0 # 非易失标志位
TPM2_PT_NV_COUNTERS_AVAIL: 0x8
TPM2_PT_ALGORITHM_SET: 0xFFFFFFFF
TPM2_PT_LOADED_CURVES: 0x3
TPM2_PT_AUDIT_COUNTER_0: 0x0 # 审计日志
TPM2_PT_AUDIT_COUNTER_1: 0x0
```

---

### 不同层级


**Owner Hierarchy**: 你平时用来创建密钥、存储数据的权限。

**Endorsement Hierarchy**: 涉及设备隐私和证书的权限。

**Lockout Hierarchy**: “锁定控制”权限，用于控制锁定策略：

- 允许多少次普通密码尝试后进入锁定模式 (TPM2_PT_MAX_AUTH_FAIL)
- 被记录下连续失败后，过多久次数才能减一 (TPM2_PT_LOCKOUT_INTERVAL)
- 进入锁定模式后，过多久才能解锁 (TPM2_PT_LOCKOUT_RECOVERY)

> ⚠️注意：如果你是在验证以上三种层级的管理密码，比如用 tpm2_clear -C o -c -p <password>的时候，只有一次机会，失败立即进入锁定模式。
> 
> 你将被限制到 TPM2_PT_LOCKOUT_RECOVERY 的时间秒数之后才能解锁。
> 这两个时间设成 0，永远解不了，只能清除。

**Platform Hierarchy**: 唯一不受 DA 限制的密码尝试。但是就算你拿到了权限，除了能够清除所有的密钥和密码，没有任何别的权限。

---

### 初始化自己的 tpm 配置

**清除**：`tpm2_clear`

有的平台可以直接用`tpm2_clear -c p`清掉，有的不行只能到 bios 里面清。

**修改锁定设置**：`tpm2_dictionarylockout` (也叫 DA，dictionary attack)

```bash
# 分别对应上面的“锁定层级”的三个变量，下例为windows标准设置
sudo tpm2_dictionarylockout -s -n 32 -t 7200 -l 86400
```

**修改密码**：`tpm2_changeauth`

```bash
sudo tpm2_changeauth -c lockout <new_password>
```

这里有个彩蛋，windows 一开始看到新的 tpm，跟我们一样改完了，直接把钥匙扔了，惊喜吧？

所以你只能重置，然后自己设个密码，好在 windows 不会改你的密码回去。

---
## 开始使用

创建主密钥，得到一个 tpm 的内存快照，这个主密钥，相比于密钥的说法，其实更是一个 token，因为是由 TPM 这一个生命周期的种子派生的，所以每次用同样的输入得到同样的输出，这里不是指的 ctx 的 hash 相同，而是每次读取的公钥相同。

如果还原了 tpm，签名会变，ctx 永远不再可用。

```bash
# 创一个新的
❯ tpm2_createprimary -C o -c primary2.ctx
name-alg:
  value: sha256
  raw: 0xb
attributes:
  value: fixedtpm|fixedparent|sensitivedataorigin|userwithauth|restricted|decrypt
  raw: 0x30072
type:
  value: rsa
  raw: 0x1
exponent: 65537
bits: 2048
scheme:
  value: null
  raw: 0x10
scheme-halg:
  value: (null)
  raw: 0x0
sym-alg:
  value: aes
  raw: 0x6
sym-mode:
  value: cfb
  raw: 0x43
sym-keybits: 128
rsa: c26b4cbadd50e487645f22d72f378953282d9a95036f09815fd91b2fd360f85517e730b19c1ba5668452b4ceca94a38aa6883ba6204f1ea4f72bd644190186fd1806f486e0e9de1ebe4fd64f618a0aac2d120e766bd0575f19b0ecce6ff55df47bacdffb8a431ac8d75cadff88ec62f149ae99ea210da4ba315b2d849b1e2b9196f7baac40ee34382f063e69af448b0c5812319b1efaa7cdffe50d3e4c396e427b270c95676b48168b2b90de555dd1cb46cbdeaed6c4f5c8466fa6a977af67a70efdf673a05b3fe7577bfb7d55991a0b7e94e917fc2533975c13c26231b3d2f6e990c395f963728f3dcaecd8f656f4a5a709fbd5c7edbda773ce960d0c9076c3

# 读一个之前创的
❯ tpm2_readpublic -c primary.ctx
name: 000bf2c2daef8da6f674f7cdd47edb780e14baec9ed14a212904d79ca92c93e05c7c
qualified name: 000b8a569c59019bf73a23befe7aeb9e54c74470737c0288f63d2481324388e1edfb
name-alg:
  value: sha256
  raw: 0xb
attributes:
  value: fixedtpm|fixedparent|sensitivedataorigin|userwithauth|restricted|decrypt
  raw: 0x30072
type:
  value: rsa
  raw: 0x1
exponent: 65537
bits: 2048
scheme:
  value: null
  raw: 0x10
scheme-halg:
  value: (null)
  raw: 0x0
sym-alg:
  value: aes
  raw: 0x6
sym-mode:
  value: cfb
  raw: 0x43
sym-keybits: 128
rsa: c26b4cbadd50e487645f22d72f378953282d9a95036f09815fd91b2fd360f85517e730b19c1ba5668452b4ceca94a38aa6883ba6204f1ea4f72bd644190186fd1806f486e0e9de1ebe4fd64f618a0aac2d120e766bd0575f19b0ecce6ff55df47bacdffb8a431ac8d75cadff88ec62f149ae99ea210da4ba315b2d849b1e2b9196f7baac40ee34382f063e69af448b0c5812319b1efaa7cdffe50d3e4c396e427b270c95676b48168b2b90de555dd1cb46cbdeaed6c4f5c8466fa6a977af67a70efdf673a05b3fe7577bfb7d55991a0b7e94e917fc2533975c13c26231b3d2f6e990c395f963728f3dcaecd8f656f4a5a709fbd5c7edbda773ce960d0c9076c3

```

### 加密文字

在主密钥下面创建一个子密钥：

```bash
echo -n "hello" | tpm2_create -C primary.ctx \
  -u key.pub -r key.priv \
  -i- \
  -p "123456"
```

生成一个 tpm 的内存快照：

```bash
tpm2_load -C primary.ctx -u key.pub -r key.priv -c key.ctx
```

把它持久化到 tpm 的对象里面：

```bash
sudo tpm2_evictcontrol -C o -c key.ctx 0x81010002
```

---
> 有点乱？总结一下

**命令**说明：
tpm2_create 指的是创建一个"密封信件",这个信件有公钥来标识身份，有加密 blob 来给 tpm 读。
tpm2_load 则是让 tpm 读取这个密封信件，他生成一个内存快照 (token)，这个东西可以持久化来被 tpm 引用（成为永久句柄）。
tpm2_evictcontrol 如果-c 加的是文件，然后再跟上地址，语义就是把这个文件持久化到 tpm 的一个句柄中；如果-c 加的是一个地址，那么则是把这个持久句柄驱逐。

对这里出现的**文件**进行说明：

- key.pub 可以开放给别人看
- key.priv 是被 tpm 加密的对象，只有 tpm 才能解密
- key.ctx 是 tpm 的内存快照，和 0x 开头的是同一个类型的东西，都可以被`-c`加载

---

所以我们给他解个密：

```bash
❯ tpm2_unseal -c key.ctx -p 123456
hello%
❯ tpm2_unseal -c 0x81010002 -p 123456
hello%  
```

### 验证签名
既然懂了一些，我们就不要用 rsa 了，用 ecc，只需把所有的创建密钥的过程加`-G ecc`就行。

如果要删除之前的，善用 evictcontrol。

重新创建 ecc 的主密钥：
```bash
tpm2_createprimary -C o -G ecc -c ecc_primary.ctx
```

创建一个签名的对象：

```bash
tpm2_create \
  -C ecc_primary.ctx \
  -G ecc256:ecdsa \
  -u ecc.pub \
  -r ecc.priv \
  -p 123456
```

加载：

```bash
tpm2_load \
  -C ecc_primary.ctx \
  -u ecc.pub \
  -r ecc.priv \
  -c ecc.ctx
```

持久化：
```bash
sudo tpm2_evictcontrol -C o -c ecc.ctx 0x81020000
```

生成一个固定的挑战，用于验证（其实真正的过程中，每次都是不同的）：

```bash
head -c 32 /dev/urandom > challenge.bin
```

用 tpm 自带的工具验证：

```bash
❯ tpm2_sign \
  -c 0x81020000 \
  -g sha256 \
  -s ecdsa \
  -o sig.tss \
  -p 123456 \
  challenge.bin
❯ tpm2_verifysignature \
  -c 0x81020000 \
  -g sha256 \
  -s sig.tss \
  -m challenge.bin
# 返回0，通过
```

---

## 整活
接下来把这个接入 pam。

导出公钥：
```bash
tpm2_readpublic -c 0x81020000 -f pem -o /etc/tpm-ecc.pub.pem
chmod 644 /etc/tpm-ecc.pub.pem
```

用我这个[项目](https://github.com/minortex/tpm_auth)试试，仅供娱乐：
```bash
#%PAM-1.0

auth       required                    pam_faillock.so      preauth
auth       [success=3 default=ignore]  pam_tpm_ecc.so       key_handle=0x81020000 pubkey=/etc/tpm-ecc.pub.pem
-auth      [success=2 default=ignore]  pam_systemd_home.so
auth       [success=1 default=bad]     pam_unix.so          try_first_pass nullok
auth       [default=die]               pam_faillock.so      authfail
auth       optional                    pam_permit.so
auth       required                    pam_env.so
auth       required                    pam_faillock.so      authsucc
```

### polkit

这玩意，搞那么复杂的权限管理，还用模板，没折腾死我。

他每次授权的时候启动一个 helper，这个 helper 有 root 权限，但是启动的时候被 systemd 限制了一大堆特权，我们得用 drop-in 给他加回来：

```bash
sudo systemctl edit polkit-agent-helper@
```

```ini
# Editing /etc/systemd/system/polkit-agent-helper@.service.d/override.conf
[Service]                        
DeviceAllow=/dev/tpmrm0 rw
BindPaths=/dev/tpmrm0
```

## 彩蛋
**一发入魄**：
```bash
❯ sudo tpm2_dictionarylockout -s -n 10 -t 600 -l 60
WARNING:esys:src/tss2-esys/api/Esys_DictionaryAttackParameters.c:310:Esys_DictionaryAttackParameters_Finish() Received TPM Error 
ERROR:esys:src/tss2-esys/api/Esys_DictionaryAttackParameters.c:108:Esys_DictionaryAttackParameters() Esys Finish ErrorCode (0x0000098e) 
ERROR: Esys_DictionaryAttackParameters(0x98E) - tpm:session(1):the authorization HMAC check failed and DA counter incremented
ERROR: Failed DictionaryLockout Setup
ERROR: Unable to run tpm2_dictionarylockout
❯ sudo tpm2_dictionarylockout -s -n 10 -t 600 -l 60
WARNING:esys:src/tss2-esys/api/Esys_DictionaryAttackParameters.c:310:Esys_DictionaryAttackParameters_Finish() Received TPM Error 
ERROR:esys:src/tss2-esys/api/Esys_DictionaryAttackParameters.c:108:Esys_DictionaryAttackParameters() Esys Finish ErrorCode (0x00000921) 
ERROR: Esys_DictionaryAttackParameters(0x921) - tpm:warn(2.0): authorizations for objects subject to DA protection are not allowed at this time because the TPM is in DA lockout mode
ERROR: Failed DictionaryLockout Setup
ERROR: Unable to run tpm2_dictionarylockout
```