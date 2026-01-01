#!/usr/bin/env node

const bitgoLib = require('bitgo-utxo-lib-z');
const fs = require('fs');

function getArg(name) {
    const index = process.argv.indexOf(name);
    return index > -1 ? process.argv[index + 1] : null;
}

const args = process.argv.slice(2);

const showHelpFlag =
    args.includes('--help') || args.includes('-h');

const generateAddress = process.argv.includes('--gen-address');
const addressFromWif = process.argv.includes('--address-from-wif');
const compressed = !process.argv.includes('--uncompressed');

const networkName = getArg('--network')?.toLowerCase();
const senderWif = getArg('--wif');
const recipientAddress = getArg('--to');
const amountToSend = parseInt(getArg('--amount'), 10);
const fee = parseInt(getArg('--fee'), 10) || 2000;
const utxoDataString = getArg('--utxos');
const utxoFilePath = getArg('--utxos-file');
const blockHeight = parseInt(getArg('--blockheight'), 10) || 0;

const NETWORKS = {
    zcash: bitgoLib.networks.zcash,
    bitcoinz: bitgoLib.networks.bitcoinz,
    litecoinz: bitgoLib.networks.litecoinz,
    zero: bitgoLib.networks.zero,
    zeroclassic: bitgoLib.networks.zeroclassic,
    zclassic: bitgoLib.networks.zclassic,
    gemlink: bitgoLib.networks.gemlink,
    ycash: bitgoLib.networks.ycash
};

const network = NETWORKS[networkName];

function showHelp() {
    console.log(`
Transaction & Address Tool
====================================

USAGE
-----

Generate a new transparent (P2PKH) address:
  wallet-cli --network <network> --gen-address [--uncompressed]

Derive address from WIF:
  wallet-cli --network <network> --address-from-wif --wif <private-key-wif>

Build and sign a transaction:
  wallet-cli --network <network> \\
    --wif <private-key-wif> \\
    --to <recipient-address> \\
    --amount <satoshis> \\
    --fee <satoshis> \\
    (--utxos '<json>' | --utxos-file <file>) \\
    [--blockheight <height>]

OPTIONS
-------

--network <name>        Network to use (default: bitcoinz)
--gen-address           Generate a new address
--address-from-wif      Derive address from WIF
--uncompressed          Generate uncompressed public key

--wif <wif>             Sender private key (WIF)
--to <address>          Recipient address
--amount <satoshis>     Amount to send (in satoshis)
--fee <satoshis>        Transaction fee (default: 2000)
--utxos <json>          UTXOs as JSON string
--utxos-file <file>     UTXOs from JSON file
--blockheight <height>  Current block height (expiry = +300)

--help, -h              Show this help message

SUPPORTED NETWORKS
------------------

${Object.keys(NETWORKS).join(', ')}
`);
}

if (showHelpFlag) {
    showHelp();
    process.exit(0);
}

if (!network) {
    console.error(
        `Unsupported network "${networkName}". Supported: ${Object.keys(NETWORKS).join(', ')}`
    );
    process.exit(1);
}

if (generateAddress) {
    try {
        const keyPair = bitgoLib.ECPair.makeRandom({
            network,
            compressed
        });

        const pubKey = keyPair.getPublicKeyBuffer();
        const pubKeyHash = bitgoLib.crypto.hash160(pubKey);

        const address = bitgoLib.address.toBase58Check(
            pubKeyHash,
            network.pubKeyHash
        );

        console.log(JSON.stringify({
            network: networkName,
            address,
            wif: keyPair.toWIF(),
            publicKey: pubKey.toString('hex'),
            compressed
        }, null, 2));

        process.exit(0);

    } catch (err) {
        console.error('Failed to generate address:', err.message);
        process.exit(1);
    }
}


if (addressFromWif) {
    try {
        if (!senderWif) {
            console.error('Missing --wif argument');
            process.exit(1);
        }

        const keyPair = bitgoLib.ECPair.fromWIF(senderWif, network);

        const pubKey = keyPair.getPublicKeyBuffer();
        const pubKeyHash = bitgoLib.crypto.hash160(pubKey);

        const address = bitgoLib.address.toBase58Check(
            pubKeyHash,
            network.pubKeyHash
        );
        console.log(address);

        process.exit(0);

    } catch (err) {
        console.error('Failed to derive address from WIF:', err.message);
        process.exit(1);
    }
}


if (!senderWif || !recipientAddress || !amountToSend || (!utxoDataString && !utxoFilePath)) {
    console.error('Missing required arguments.');
    process.exit(1);
}

let rawUtxos;
try {
    if (utxoFilePath) {
        const content = fs.readFileSync(utxoFilePath, 'utf8');
        rawUtxos = JSON.parse(content);
    } else {
        rawUtxos = JSON.parse(utxoDataString);
    }
} catch (e) {
    console.error('Failed to read UTXOs:', e.message);
    process.exit(1);
}

const utxos = rawUtxos.map(u => ({
    txid: String(u.txid),
    vout: Number(u.vout),
    value: Number(u.satoshis)
}));

try {
    const keyPair = bitgoLib.ECPair.fromWIF(senderWif, network);
    const txb = new bitgoLib.TransactionBuilder(network);

    txb.setVersion(bitgoLib.Transaction.ZCASH_SAPLING_VERSION);
    txb.setVersionGroupId(0x892F2085);
    txb.setExpiryHeight(blockHeight + 300);

    let totalInput = 0;
    for (const u of utxos) {
        txb.addInput(u.txid, u.vout);
        totalInput += u.value;
    }

    txb.addOutput(recipientAddress, amountToSend);

    const changeAmount = totalInput - amountToSend - fee;
    if (changeAmount > 1000) {
        txb.addOutput(keyPair.getAddress(), changeAmount);
    }

    for (let i = 0; i < utxos.length; i++) {
        txb.sign(
            i,
            keyPair,
            null,
            bitgoLib.Transaction.SIGHASH_ALL,
            utxos[i].value
        );
    }

    const tx = txb.build();
    console.log(tx.toHex());

} catch (error) {
    console.error('An error occurred:', error.message);
    process.exit(1);
}
