//-----------------------------------------------------------------------------
// Borrowed initially from Arduino SPIFlash Library v.2.5.0
// Copyright (C) 2015 by Prajwal Bhattaram.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// See LICENSE.txt for the text of the license.
//-----------------------------------------------------------------------------
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//
//                      Common Instructions                           //
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//
#ifndef __FLASHMEM_H
#define __FLASHMEM_H

#include "common.h"

//    Used Command
#define ID              0x90
#define MANID           0x90
#define JEDECID         0x9F

#define READSTAT1       0x05
#define READSTAT2       0x35
#define WRITESTAT       0x01

#define WRITEDISABLE    0x04
#define WRITEENABLE     0x06

#define READDATA        0x03
#define FASTREAD        0x0B
#define PAGEPROG        0x02

#define SECTORERASE     0x20
#define BLOCK32ERASE    0x52
#define BLOCK64ERASE    0xD8
#define CHIPERASE       0xC7

#define UNIQUE_ID       0x4B

//    Not used or not support command
#define RELEASE         0xAB
#define POWERDOWN       0xB9
#define SUSPEND         0x75
#define RESUME          0x7A

// Flash busy timeout: 20ms is the strict minimum when writing 256kb
#define BUSY_TIMEOUT    200000L

#define PAGESIZE        0x100
#define WINBOND_WRITE_DELAY 0x02

#define SPI_CLK         48000000

#define BUSY            0x01
#define WRTEN           0x02
#define SUS             0x40

#define DUMMYBYTE       0xEE
#define NULLBYTE        0x00
#define NULLINT         0x0000
#define NO_CONTINUE     0x00
#define PASS            0x01
#define FAIL            0x00
#define maxAddress      capacity

//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//
//                            List of Error codes                          //
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//
#define SUCCESS         0x00
#define CALLBEGIN       0x01
#define UNKNOWNCHIP     0x02
#define UNKNOWNCAP      0x03
#define CHIPBUSY        0x04
#define OUTOFBOUNDS     0x05
#define CANTENWRITE     0x06
#define PREVWRITTEN     0x07
#define LOWRAM          0x08
#define NOSUSPEND       0x09
#define UNKNOWNERROR    0xFF

// List of blocks
#define MAX_BLOCKS      4
#define MAX_SECTORS     16

//#define FLASH_BAUD 24000000
#define FLASH_MINFAST 24000000 //33000000
#define FLASH_BAUD MCK/2
#define FLASH_FASTBAUD MCK
#define FLASH_MINBAUD FLASH_FASTBAUD

//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//

bool FlashInit(void);
void Flash_UniqueID(uint8_t *uid);
void FlashStop(void);

void FlashSetup(uint32_t baudrate);
bool Flash_CheckBusy(uint32_t timeout);
uint8_t Flash_ReadStat1(void);
uint16_t FlashSendByte(uint32_t data);
uint16_t FlashSendLastByte(uint32_t data);


#ifndef AS_BOOTROM
void FlashmemSetSpiBaudrate(uint32_t baudrate);
bool Flash_WaitIdle(void);
void Flash_TransferAdresse(uint32_t address);

void Flash_WriteEnable(void);
bool Flash_WipeMemoryPage(uint8_t page);
bool Flash_WipeMemory(void);
bool Flash_Erase4k(uint8_t block, uint8_t sector);
//bool Flash_Erase32k(uint32_t address);
bool Flash_Erase64k(uint8_t block);

typedef struct {
    uint8_t manufacturer_id;
    uint8_t device_id;
    uint8_t device_id2;
} flash_device_type_t; // extra device_id used for the JEDEC ID read via cmd 9F
bool Flash_ReadID(flash_device_type_t *result, bool read_jedec);

uint16_t Flash_ReadData(uint32_t address, uint8_t *out, uint16_t len);
uint16_t Flash_ReadDataCont(uint32_t address, uint8_t *out, uint16_t len);
uint16_t Flash_Write(uint32_t address, uint8_t *in, uint16_t len);
uint16_t Flash_WriteData(uint32_t address, uint8_t *in, uint16_t len);
uint16_t Flash_WriteDataCont(uint32_t address, uint8_t *in, uint16_t len);
void Flashmem_print_status(void);
void Flashmem_print_info(void);

typedef struct {
    uint8_t  manufacturer_id;
    uint8_t  device_id;
    uint16_t jedec_id;
    uint8_t  pages64k;
    char    *device;
} spi_flash_t;

static const spi_flash_t SpiFlashTable[] = {
    // first element is the default of 4 * 64kB pages (256kB)
    { 0x00, 0x00, 0x0000,  4, "unknown" },     //  256k
    // Manufacturer: Puya
    { 0x85, 0x00, 0x6015, 32, "P25Q16H" },     // 2048k
    /// Manufacturer: Renesas
    { 0x1F, 0x46, 0x0000, 32, "AT25XE161D" },  // 2048k
    { 0x1F, 0x47, 0x0000, 64, "AT25XE321D" },  // 4096k
    // Manufacturer: Winbond
    { 0xEF, 0x00, 0x3012,  4, "W25X20BV" },    //  256k
    { 0xEF, 0x00, 0x3013,  8, "W25X40BV" },    //  512k

    { 0xEF, 0x00, 0x4013,  8, "W25Q40BV" },    //  512k
    { 0xEF, 0x00, 0x4014, 16, "W25Q80BV" },    // 1024k
    { 0xEF, 0x14, 0x4015, 32, "W25Q16BV" },    // 2048k
    { 0xEF, 0x15, 0x4016, 64, "W25Q32BV" },    // 4096k

    { 0xEF, 0x21, 0x7022,  4, "W25Q02JV" },
    // identified by Manufacturer /Device ID
//    { 0xEF, 0x05, 0x0000,  1, "Winbond!!!" },
    { 0xEF, 0x10, 0x0000,  2, "W25*10BV!!!" }, //  128k
    { 0xEF, 0x11, 0x0000,  4, "W25*20BV" },    //  256k
    { 0xEF, 0x12, 0x0000,  8, "W25*40BV" },    //  512k
    { 0xEF, 0x13, 0x0000, 16, "W25*80BV" }     // 1024k
};

extern uint8_t spi_flash_pages64k;

bool FlashDetect(void);

#ifndef ARRAYLEN
# define ARRAYLEN(x) (sizeof(x)/sizeof((x)[0]))
#endif

#endif // #ifndef AS_BOOTROM

#endif
