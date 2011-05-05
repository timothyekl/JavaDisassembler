#!/usr/bin/env python3.1

import struct
import sys

DEBUG = True

def error(strList):
    for s in strList:
        print(s)
    quit(-1)

def debug(strList):
    if DEBUG:
        for s in strList:
            print(s)
        print()

def bytepos(bytesIdx, classBytes):
    if DEBUG:
        print("Read {0}/{1} bytes in class file".format(bytesIdx, len(classBytes)))
        print()

def b16toui(b):
    if len(b) != 2:
        return 0
    else:
        return b[0] * 256 + b[1]
def b32tosi(b):
    v = b[0] << 24 + b[1] << 16 + b[2] << 8 + b[3]
    if v > (2 ** 31):
        v -= (2 ** 32)
    return v

if len(sys.argv) != 2:
    error(["Usage: {0} <class file>".format(sys.argv[0])])

# Read in raw class file
infile = sys.argv[1]
with open(infile, 'rb') as classFile:
    classBytes = classFile.read()
debug(["Found bytes: {0}".format(classBytes)])

# Check magic number for Java class file
magicNumber = classBytes[0:4]
if magicNumber != b'\xca\xfe\xba\xbe':
    error(["Invalid magic number: '{0}'".format(magicNumber.decode("ascii")), "Did you supply a valid Java class file?"])
debug(["Checked magic number: CAFEBABE"])

# Check JVM major/minor version
minorVersion = b16toui(classBytes[4:6])
majorVersion = b16toui(classBytes[6:8])
majorVersions = {
    50 : "J2SE 6.0",
    49 : "J2SE 5.0",
    48 : "JDK 1.4",
    47 : "JDK 1.3",
    46 : "JDK 1.2",
    45 : "JDK 1.1"
}
if majorVersion not in majorVersions.keys():
    error(["Invalid major version: {0}".format(majorVersion)])
debug([
    "Using Java major version: {0} ({1})".format(majorVersion, majorVersions[majorVersion]), 
    "Using Java minor version: {0}".format(minorVersion)
])

# Handle constant pool
constantPoolCount = b16toui(classBytes[8:10])

bytesIdx = 10
constantTags = {
    1 : 'string',
    3 : 'integer',
    4 : 'float',
    5 : 'long',
    6 : 'double',
    7 : 'class-reference',
    8 : 'string-reference',
    9 : 'field-reference',
    10 : 'method-reference',
    11 : 'interface-method-reference',
    12 : 'name-type-descriptor'
}
constantSizes = {
    1 : 2,
    3 : 4,
    4 : 4,
    5 : 8,
    6 : 8,
    7 : 2,
    8 : 2,
    9 : 4,
    10 : 4,
    11 : 4,
    12 : 4
}
constantEvaluate = {
    1 : (lambda x : x.decode("utf-8")),
    3 : (lambda x : struct.unpack("!i", x)[0]),
    4 : (lambda x : struct.unpack("!f", x)[0]),
    5 : (lambda x : struct.unpack("!q", x)[0]),
    6 : (lambda x : struct.unpack("!d", x)[0]),
    7 : (lambda x : b16toui(x)),
    8 : (lambda x : b16toui(x)),
    9 : (lambda x : (b16toui(x[0:2]), b16toui(x[2:4]))),
    10 : (lambda x : (b16toui(x[0:2]), b16toui(x[2:4]))),
    11 : (lambda x : (b16toui(x[0:2]), b16toui(x[2:4]))),
    12 : (lambda x : (b16toui(x[0:2]), b16toui(x[2:4]))),
}
constantPool = []
for i in range(constantPoolCount - 1):
    tag = classBytes[bytesIdx]
    bytesIdx += 1

    if tag == 1:
        stringSize = b16toui(classBytes[bytesIdx:bytesIdx+2])
        bytesIdx += 2
        cpStr = classBytes[bytesIdx:bytesIdx+stringSize].decode("utf-8")
        bytesIdx += stringSize
        cpItem = (constantTags[tag], cpStr)
    else:
        cpBytes = classBytes[bytesIdx:bytesIdx + constantSizes[tag]]
        bytesIdx += constantSizes[tag]
        cpValue = constantEvaluate[tag](cpBytes)
        cpItem = (constantTags[tag], constantEvaluate[tag](cpBytes))

    constantPool.append(cpItem)

msgs = ["Constant pool has {0} items".format(constantPoolCount)]
msgs.extend(["    {0} : {1}".format(i + 1, constantPool[i]) for i in range(constantPoolCount - 1)])
#msgs.append("Now at bytes index: {0}/{1}".format(bytesIdx, len(classBytes)))
debug(msgs)

# Handle class attributes
accessFlagBytes = classBytes[bytesIdx:bytesIdx + 2]
thisClassIdx = b16toui(classBytes[bytesIdx + 2:bytesIdx + 4])
superClassIdx = b16toui(classBytes[bytesIdx + 4:bytesIdx + 6])
bytesIdx += 6

debug([
    "Access flags: {0}".format(hex(b16toui(accessFlagBytes))),
    "Reference to 'this' class: {0} => {1}".format(thisClassIdx, constantPool[thisClassIdx - 1]),
    "Reference to 'super' class: {0} => {1}".format(superClassIdx, constantPool[superClassIdx - 1])
])

# Handle interface table
interfaceTableCount = b16toui(classBytes[bytesIdx:bytesIdx + 2])
bytesIdx += 2
debug(["Interface table has {0} entries".format(interfaceTableCount)])
if interfaceTableCount != 0:
    raise Exception("Unimplemented!")

# Handle field table
fieldTableCount = b16toui(classBytes[bytesIdx:bytesIdx + 2])
bytesIdx += 2
debug(["Field table has {0} entries".format(fieldTableCount)])
if fieldTableCount != 0:
    raise Exception("Unimplemented!")

# Handle method table
methodTableCount = b16toui(classBytes[bytesIdx:bytesIdx + 2])
bytesIdx += 2
debug(["Method table has {0} entries".format(methodTableCount)])
for i in range(methodTableCount):
    methodAccessFlags = b16toui(classBytes[bytesIdx:bytesIdx + 2])
    methodNameIdx = b16toui(classBytes[bytesIdx + 2:bytesIdx + 4])
    methodDescriptorIdx = b16toui(classBytes[bytesIdx + 4:bytesIdx + 6])
    methodAttrCount = b16toui(classBytes[bytesIdx + 6:bytesIdx + 8])
    bytesIdx += 8

    methodAttrs = []
    for j in range(methodAttrCount):
        attrNameIdx = b16toui(classBytes[bytesIdx:bytesIdx + 2])
        attrLength = struct.unpack("!I", classBytes[bytesIdx + 2:bytesIdx + 6])[0]
        attrInfo = classBytes[bytesIdx + 6:bytesIdx + 6 + attrLength]
        bytesIdx += 6 + attrLength
        methodAttrs.append((attrNameIdx, attrLength, attrInfo))

    msgs = [
        "Method:",
        "    Access flags: {0}".format(hex(methodAccessFlags)),
        "    Name: {0} => {1}".format(methodNameIdx, constantPool[methodNameIdx - 1]),
        "    Descriptor: {0} => {1}".format(methodDescriptorIdx, constantPool[methodDescriptorIdx - 1]),
        "    Additional attributes: {0}".format(methodAttrCount)
    ]
    msgs.extend(["        Attr: {0}".format(methodAttr) for methodAttr in methodAttrs])
    debug(msgs)

# Handle attributes table
attrTableCount = b16toui(classBytes[bytesIdx:bytesIdx + 2])
bytesIdx += 2
attrs = []
for i in range(attrTableCount):
    attrNameIdx = b16toui(classBytes[bytesIdx:bytesIdx + 2])
    attrLength = struct.unpack("!I", classBytes[bytesIdx + 2:bytesIdx + 6])[0]
    attrInfo = classBytes[bytesIdx + 6:bytesIdx + 6 + attrLength]
    bytesIdx += 6 + attrLength
    attrs.append((attrNameIdx, attrLength, attrInfo))
msgs = ["Attributes table has {0} entries:".format(attrTableCount)]
msgs.extend(["    {0}".format(attr) for attr in attrs])
debug(msgs)

# Error-check
if bytesIdx != len(classBytes):
    error("Finished disassembling, but didn't read all bytes from file")
