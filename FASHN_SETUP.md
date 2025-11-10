# <¨ FASHN API Integration Guide

## 'B> 87<5=8;>AL?

@8;>65=85 **Tap to look** B5?5@L 8A?>;L7C5B **FASHN API** 2<5AB> IDM-VTON 4;O <0:A8<0;L=>3> :0G5AB20 28@BC0;L=>9 ?@8<5@:8!

###  @58<CI5AB20 FASHN API

- **KA>G09H55 :0G5AB2>**:  50;8AB8G=K5 @57C;LB0BK 157 0@B5D0:B>2
- **KAB@0O >1@01>B:0**: 5-17 A5:C=4 (2<5AB> 30-40 A5:C=4)
- **KA>:>5 @07@5H5=85**: 864×1296 ?8:A5;59
- **@>D5AA8>=0;L=>5 :0G5AB2>**: >4E>48B 4;O e-commerce
- **0456=>ABL**: !B018;L=0O @01>B0 8 B5E?>445@6:0

---

## =Ë (03 1: >;CG5=85 API :;NG0

### 1.1  538AB@0F8O =0 FASHN

1. 5@5948B5 =0 A09B: **https://fashn.ai/**
2. 06<8B5 **"Get Started"** 8;8 **"Sign Up"**
3. 0@538AB@8@C9B5AL 8A?>;L7CO email
4. >4B25@48B5 email 04@5A

### 1.2 >;CG5=85 API :;NG0

1. >948B5 2 0::0C=B FASHN
2. 5@5948B5 2 API Dashboard: **https://app.fashn.ai/api**
3. 06<8B5 **"Create API Key"** 8;8 **"Get API Key"**
4. !:>?8@C9B5 20H API :;NG (>= 1C45B 2845= B>;L:> >48= @07!)

### 1.3 >:C?:0 :@548B>2

FASHN 8A?>;L7C5B A8AB5<C :@548B>2:

**"0@8D=K5 ?;0=K:**
- **"5AB8@>20=85**: $7.50 (<8=8<C<, 157 ?@82O7:8 :0@BK)
- **On-Demand**: $0.075 70 87>1@065=85
- **Tier I**: $19/<5AOF - 282 87>1@065=8O + 10% A:84:0 =0 ?@52KH5=85
- **Tier II**: $249/<5AOF - 4,150 87>1@065=89 + 20% A:84:0
- **Tier III**: $1,249/<5AOF - 25,594 87>1@065=8O + 35% A:84:0

**;O =0G0;0:**
1.  API Dashboard =06<8B5 **"Purchase Credits"**
2. K15@8B5 ?;0= (@5:><5=4CN =0G0BL A $7.50 4;O B5AB>2)
3. ?;0B8B5 G5@57 ?;0B56=CN A8AB5<C

---

## =' (03 2: 0AB@>9:0 ;>:0;L=>3> >:@C65=8O

### 2.1 !>740=85 .env D09;0

 :>@=52>9 ?0?:5 ?@>5:B0 A>7409B5 D09; `.env`:

```bash
cd C:\Users\ivmaf\virtual-tryon-app
copy .env.example .env
```

### 2.2 >102;5=85 API :;NG0

B:@>9B5 D09; `.env` 8 2AB02LB5 20H API :;NG:

```env
# FASHN API Configuration
FASHN_API_KEY=fashn_live_1234567890abcdefghijklmnopqrstuvwxyz

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

**:** 0<5=8B5 `fashn_live_1234567890abcdefghijklmnopqrstuvwxyz` =0 20H @50;L=K9 API :;NG!

### 2.3 #AB0=>2:0 7028A8<>AB59

```bash
# :B828@C9B5 28@BC0;L=>5 >:@C65=85
cd C:\Users\ivmaf\virtual-tryon-app
call venv\Scripts\activate

# #AB0=>28B5 >1=>2;5==K5 7028A8<>AB8
pip install --upgrade pip
pip install -r requirements.txt
```

### 2.4 >:0;L=>5 B5AB8@>20=85

```bash
# 0?CAB8B5 A5@25@
python backend\app.py

# B:@>9B5 2 1@0C75@5
# http://localhost:5000
```

---

##  (03 3:  0725@BK20=85 =0 Railway

### 3.1 >102;5=85 ?5@5<5==>9 >:@C65=8O =0 Railway

1. B:@>9B5 ?@>5:B =0 **Railway**: https://railway.app/dashboard
2. K15@8B5 20H ?@>5:B **taptolook**
3. 5@5948B5 2 **Variables** (2:;04:0 A;520)
4. 06<8B5 **"New Variable"**
5. >102LB5 ?5@5<5==CN:
   - **Name**: `FASHN_API_KEY`
   - **Value**: 20H API :;NG (=0?@8<5@: `fashn_live_1234567890...`)
6. 06<8B5 **"Add"**

### 3.2 03@C7:0 >1=>2;5==>3> :>40

```bash
cd C:\Users\ivmaf\virtual-tryon-app

# >102LB5 2A5 87<5=5=8O
git add .

# !>7409B5 :><<8B
git commit -m "Upgrade: Integrate FASHN API for better quality and speed"

# 03@C78B5 =0 GitHub
git push
```

### 3.3 2B><0B8G5A:>5 @0725@BK20=85

Railway 02B><0B8G5A:8:
1. 1=0@C68B 87<5=5=8O 2 GitHub
2. 5@5A>15@5B ?@8;>65=85
3.  0725@=5B =>2CN 25@A8N A FASHN API

>4>648B5 3-5 <8=CB 4;O 7025@H5=8O 45?;>O.

### 3.4 @>25@:0 @01>BK

1. B:@>9B5 20H URL: **https://taptolook.up.railway.app**
2. 03@C78B5 D>B> G5;>25:0 8 >4564K
3. 06<8B5 **"@8<5@8BL >4564C"**
4.  57C;LB0B ?>O28BAO G5@57 5-17 A5:C=4

---

## = @>25@:0 =0AB@>9:8

### @>25@:0 ;>:0;L=>

```bash
# 0?CAB8B5 Python 2 28@BC0;L=>< >:@C65=88
python

# K?>;=8B5 ?@>25@:C
>>> import os
>>> from dotenv import load_dotenv
>>> load_dotenv()
>>> api_key = os.getenv('FASHN_API_KEY')
>>> print(f"API Key loaded: {api_key[:15]}..." if api_key else "API Key not found!")
>>> exit()
```

K 4>;6=K C2845BL: `API Key loaded: fashn_live_1234...`

### @>25@:0 =0 Railway

1. B:@>9B5 **Railway Dashboard**
2. 5@5948B5 2 **Deployments**
3. B:@>9B5 ?>A;54=89 45?;>9
4. @>25@LB5 ;>38:
   - 5 4>;6=> 1KBL >H81:8 `FASHN_API_KEY not set`
   - @8 703@C7:5 87>1@065=89 4>;6=> ?>O28BLAO: `Sending request to FASHN API...`
   - 0B5<: `Prediction started, ID: xxx`
   - : `Status: completed`

---

##   #AB@0=5=85 ?@>1;5<

### @>1;5<0 1: "FASHN_API_KEY not set"

**@8G8=0:** API :;NG =5 CAB0=>2;5= 2 ?5@5<5==KE >:@C65=8O

** 5H5=85:**
- **>:0;L=>**: @>25@LB5 D09; `.env` 8 C1548B5AL GB> :;NG ?@028;L=K9
- **Railway**: @>25@LB5 Variables 2 Railway Dashboard, 4>102LB5 `FASHN_API_KEY`

### @>1;5<0 2: "FASHN API error: 401"

**@8G8=0:** 525@=K9 8;8 =50:B82=K9 API :;NG

** 5H5=85:**
1. @>25@LB5 ?@028;L=>ABL :;NG0 (A:>?8@C9B5 70=>2> A FASHN Dashboard)
2. #1548B5AL GB> C 20A 5ABL 0:B82=K5 :@548BK =0 10;0=A5
3. @>25@LB5 GB> :;NG =5 8AB5:

### @>1;5<0 3: "FASHN API error: 402"

**@8G8=0:** 54>AB0B>G=> :@548B>2 =0 10;0=A5

** 5H5=85:**
1. 5@5948B5 =0 https://app.fashn.ai/api
2. @>25@LB5 10;0=A :@548B>2
3. >?>;=8B5 10;0=A 5A;8 =5>1E>48<>

### @>1;5<0 4: Timeout ?>A;5 2 <8=CB

**@8G8=0:** FASHN API =5 CA?5; >1@01>B0BL 70?@>A

** 5H5=85:**
- @>25@LB5 @07<5@ 703@C605<KE 87>1@065=89 (@5:><5=4C5BAO < 5MB)
- >?@>1C9B5 A=>20 (2>7<>6=0 2@5<5==0O ?5@53@C7:0 API)
- #<5=LH8B5 @07@5H5=85 87>1@065=89 ?5@54 703@C7:>9

### @>1;5<0 5:  57C;LB0B =87:>3> :0G5AB20

**@8G8=0:** 87:>5 :0G5AB2> 8AE>4=KE 87>1@065=89

** 5H5=85:**
- A?>;L7C9B5 G5B:85 D>B>3@0D88 2 ?>;=K9 @>AB
- #1548B5AL GB> >A25I5=85 E>@>H55
- $>= 4>;65= 1KBL ?@>ABK< (>4=>B>==K9 ?@54?>GB8B5;L=>)
- 45640 4>;6=0 1KBL E>@>H> 284=0 =0 D>B>

---

## =Ê >=8B>@8=3 8A?>;L7>20=8O

###  FASHN Dashboard

1. B:@>9B5 https://app.fashn.ai/api
2.  0745; **"Usage"** ?>:07K205B:
   - >;8G5AB2> 70?@>A>2 70 ?5@8>4
   - AB02H85AO :@548BK
   - AB>@8O 8A?>;L7>20=8O
3.  0745; **"API Logs"** ?>:07K205B:
   - A5 70?@>AK : API
   - !B0BCAK 2K?>;=5=8O
   - H81:8 (5A;8 1K;8)

###  Railway Logs

1. B:@>9B5 Railway Dashboard
2. 5@5948B5 2 **Deployments** ’ **View Logs**
3. $8;LB@C9B5 ?>:
   - `FASHN` - C2848B5 2A5 70?@>AK : FASHN API
   - `Status:` - AB0BCAK >1@01>B:8
   - `Error` - ;N1K5 >H81:8

---

## =¡ !>25BK ?> >?B8<870F88

### 1. ?B8<870F8O 87>1@065=89

5@54 703@C7:>9 A>6<8B5 87>1@065=8O:
-  5:><5=4C5<>5 @07@5H5=85: 1024×1536 8;8 <5=LH5
- $>@<0B: JPG (<5=LH5 @07<5@) 8;8 PNG (;CGH5 :0G5AB2>)
-  07<5@ D09;0: < 5MB

### 2. 5H8@>20=85 @57C;LB0B>2

 0AA<>B@8B5 2>7<>6=>ABL A>E@0=5=8O @57C;LB0B>2 GB>1K =5 >1@010BK20BL >4=8 8 B5 65 87>1@065=8O 42064K.

### 3. #?@02;5=85 :@548B0<8

- BA;568209B5 8A?>;L7>20=85 G5@57 Dashboard
- #AB0=>28B5 ;8<8BK 2 :>45 5A;8 =5>1E>48<>
- A?>;L7C9B5 ?>4E>4OI89 B0@8D=K9 ?;0=

### 4. 1@01>B:0 >H81>:

"5:CI0O @50;870F8O 2:;NG05B:
- 2B><0B8G5A:85 ?>2B>@=K5 ?>?KB:8 ?@8 A5B52KE >H81:0E
- "09<0CBK 4;O ?@54>B2@0I5=8O 7028A0=8O
- 5B0;L=>5 ;>38@>20=85 4;O >B;04:8

---

## = 57>?0A=>ABL

### 06=K5 ?@028;0:

1. **** =5 :><<8BLB5 `.env` D09; 2 Git
2. **** =5 ?C1;8:C9B5 API :;NG 2 :>45
3. **!** 8A?>;L7C9B5 ?5@5<5==K5 >:@C65=8O
4. **!** 45@68B5 `.env` 2 `.gitignore`

### @>25@:0 157>?0A=>AB8:

```bash
# #1548B5AL GB> .env 2 .gitignore
cd C:\Users\ivmaf\virtual-tryon-app
type .gitignore | findstr .env
```

>;65= 2K25AB8: `.env`

---

## =Þ >445@6:0

### FASHN Support

- >:C<5=B0F8O: https://docs.fashn.ai/
- Email: support@fashn.ai
- Discord: https://discord.gg/fashn (5A;8 4>ABC?=>)

### >;57=K5 AAK;:8

- FASHN Dashboard: https://app.fashn.ai/api
- FASHN API Docs: https://docs.fashn.ai/api-reference
- FASHN Pricing: https://fashn.ai/products/api
- Railway Dashboard: https://railway.app/dashboard

---

##  >=B@>;L=K9 A?8A>:

5@54 70?CA:>< 2 ?@>40:H= C1548B5AL:

- [ ] API :;NG ?>;CG5= 8 A>E@0=5=
- [ ] @548BK :C?;5=K =0 FASHN
- [ ] $09; `.env` A>740= ;>:0;L=> A ?@028;L=K< :;NG><
- [ ] 5@5<5==0O `FASHN_API_KEY` 4>102;5=0 =0 Railway
- [ ] >4 703@C65= =0 GitHub
- [ ] Railway CA?5H=> @0725@=C; =>2CN 25@A8N
- [ ] "5AB>20O ?@8<5@:0 @01>B05B :>@@5:B=>
- [ ]  57C;LB0BK 2KA>:>3> :0G5AB20
- [ ] @5<O >1@01>B:8 ~5-17 A5:C=4
- [ ] `.env` 2 `.gitignore` 8 =5 703@C65= 2 Git

---

## <‰ >B>2>!

"5?5@L 20H5 ?@8;>65=85 8A?>;L7C5B FASHN API 4;O <0:A8<0;L=>3> :0G5AB20 28@BC0;L=>9 ?@8<5@:8!

**;NG52K5 C;CGH5=8O:**
-  0G5AB2> @57C;LB0B>2 7=0G8B5;L=> 2KH5
-  !:>@>ABL >1@01>B:8 2 3-4 @070 1KAB@55
-  5=LH5 0@B5D0:B>2 8 >H81>:
-  @>D5AA8>=0;L=>5 :0G5AB2> 4;O e-commerce

**!B>8<>ABL:**
- @8<5@=> $0.075 70 >4=> 87>1@065=85
- ;O 100 ?@8<5@>: = $7.50
- ;O 1000 ?@8<5@>: = $75

**5@A8O ?@8;>65=8O:** Tap to look A0.02 (FASHN API)
