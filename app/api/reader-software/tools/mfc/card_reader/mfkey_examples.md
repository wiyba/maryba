## Sample trace
```
 +  50422:    :     26
 +     64:   0: TAG 04  00
 +    944:    :     93  20
 +     64:   0: TAG 9c  59  9b  32  6c
 +   1839:    :     93  70  9c  59  9b  32  6c  6b  30
 +     64:   0: TAG 08  b6  dd
 +   3783:    :     60  32  64  69
 +    113:   0: TAG 82  a4  16  6c
 +   1287:    :     a1  e4  58  ce  6e  ea  41  e0
 +     64:   0: TAG 5c  ad  f4  39
```
Usage with sample trace:
`./mfkey64 9C599B32 82A4166C A1E458CE 6EEA41E0 5CADF439`

## Other examples

For mfkey32, you want to get two different NR_0/NR_1 values.

```
#         <uid>    <nt>     <{nr_0}> <{ar}_0> <{nr_1}> <{ar}_1>
./mfkey32 57DA41DA 01200145 7B70C62C 909121F2 F9206A8B 908B8981
```

For mfkey32v2 (moebius), you want to get two different NT/NT1 values. (like in the SIM commands)
```
#           <uid>    <nt>     <nr_0>   <ar_0>   <nt1>    <nr_1>   <ar_1>
./mfkey32v2 12345678 1AD8DF2B 1D316024 620EF048 30D6CB07 C52077E2 837AC61A
./mfkey32v2 52B0F519 5417D1F8 4D545EA7 E15AC8C2 A1BA88C6 DAC1A7F4 5AE5C37F
```

For mfkey64, you want to have the AT response from tag.
```
#         <uid>    <nt>     <nr>     <ar>     <at>
./mfkey64 9C599B32 82A4166C A1E458CE 6EEA41E0 5CADF439
./mfkey64 52B0F519 5417D1F8 4D545EA7 E15AC8C2 5056E41B
```

### Communication decryption
A new functionality from @zhovner

Example: given the following trace
```
RDR 26
TAG 04 00
RDR 93 20
TAG 14 57 9f 69 b5
RDR 93 70 14 57 9f 69 b5 2e 51
TAG 08 b6 dd
RDR 60 14 50 2d
TAG ce 84 42 61
RDR f8 04 9c cb 05 25 c8 4f
TAG 94 31 cc 40
RDR 70 93 df 99
TAG 99 72 42 8c e2 e8 52 3f 45 6b 99 c8 31 e7 69 dc ed 09
RDR 8c a6 82 7b
TAG ab 79 7f d3 69 e8 b9 3a 86 77 6b 40 da e3 ef 68 6e fd
RDR c3 c3 81 ba
TAG 49 e2 c9 de f4 86 8d 17 77 67 0e 58 4c 27 23 02 86 f4
RDR fb dc d7 c1
TAG 4a bd 96 4b 07 d3 56 3a a0 66 ed 0a 2e ac 7f 63 12 bf
RDR 9f 91 49 ea
```

`./mfkey64 14579f69 ce844261 f8049ccb 0525c84f 9431cc40 7093df99 9972428ce2e8523f456b99c831e769dced09 8ca6827b ab797fd369e8b93a86776b40dae3ef686efd c3c381ba 49e2c9def4868d1777670e584c27230286f4 fbdcd7c1 4abd964b07d3563aa066ed0a2eac7f6312bf 9f9149ea`

```
Recovering key for:
  uid: 14579f69
   nt: ce844261
 {nr}: f8049ccb
 {ar}: 0525c84f
 {at}: 9431cc40
{enc0}: 7093df99
{enc1}: 9972428ce2e8523f456b99c831e769dced09
{enc2}: 8ca6827b
{enc3}: ab797fd369e8b93a86776b40dae3ef686efd
{enc4}: c3c381ba
{enc5}: 49e2c9def4868d1777670e584c27230286f4
{enc6}: fbdcd7c1
{enc7}: 4abd964b07d3563aa066ed0a2eac7f6312bf
{enc8}: 9f9149ea

LFSR successors of the tag challenge:
   ar: 76d4468d
   at: d5f3c476

Keystream used to generate {ar} and {at}:
  ks2: 73f18ec2
  ks3: 41c20836

Decrypted communication:
{dec0}: 3014a7fe
{dec1}: c26935cfdb95c4b4a27a84b8217ae9e48217
{dec2}: 30152eef
{dec3}: 493167c536c30f8e220b09675687067d4b31
{dec4}: 3016b5dd
{dec5}: 493167c536c30f8e220b09675687067d4b31
{dec6}: 30173ccc
{dec7}: 0000000000007e178869000000000000c4f2
{dec8}: 61148834

Found Key: [091e639cb715]
```
### Recovering partial nested authentication
A new functionality from @doegox

In some situations, we may replay a {nT} in a nested authentication, of which we know the plain nT but not the key.

Example:
```
Tag |ab! b3! 0b! D1                        |     | AUTH: nt (enc)
Rdr |46  03  39  66  AD  c1! 81  62!       |     | AUTH: nr ar (enc)
```

```
./mfkey32v2nested 5C467F63 4bbf8a12 abb30bd1 46033966 adc18162
MIFARE Classic key recovery - known nT scenario
Recover key from one reader authentication answer only
Recovering key for:
    uid: 5c467f63
     nt: 4bbf8a12
   {nt}: abb30bd1
   {nr}: 46033966
   {ar}: adc18162

LFSR successor of the tag challenge:
     ar: 77cc87f8

Keystream used to generate {nt}:
    ks0: e00c81c3

Keystream used to generate {ar}:
    ks2: da0d069a

Found Key: [059e2905bfcc]
```
