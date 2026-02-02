#!/usr/bin/env node

const bitgoLib = require('bitgo-utxo-lib-z');
const fs = require('fs');

function getArg(name) {
    const index = process.argv.indexOf(name);
    return index > -1 ? process.argv[index + 1] : null;
}

function loadUtxos(utxoDataString, utxoFilePath) {
    let raw;
    if (utxoFilePath) {
        raw = JSON.parse(fs.readFileSync(utxoFilePath, 'utf8'));
    } else {
        raw = JSON.parse(utxoDataString);
    }
    return raw.map(u => ({
        txid: String(u.txid),
        vout: Number(u.vout),
        value: Number(u.satoshis)
    }));
}

const args = process.argv.slice(2);

const showHelpFlag = args.includes('--help') || args.includes('-h');

const generateAddress = args.includes('--gen-address');
const addressFromWif = args.includes('--address-from-wif');
const generateMultisig = args.includes('--gen-multisig');

const createSigned = args.includes('--create-signed');
const createUnsigned = args.includes('--create-unsigned');
const signPartial = args.includes('--sign');
const finalizeTx = args.includes('--finalize');

const compressed = !args.includes('--uncompressed');

const networkName = getArg('--network')?.toLowerCase();
const senderWif = getArg('--wif');
const recipientAddress = getArg('--to');

const amountToSend = parseInt(getArg('--amount'), 10);
const fee = parseInt(getArg('--fee'), 10) || 2000;
const blockHeight = parseInt(getArg('--blockheight'), 10) || 0;

const utxoDataString = getArg('--utxos');
const utxoFilePath = getArg('--utxos-file');

const rawTxHex = getArg('--rawtx');
const redeemScriptHex = getArg('--redeem-script');

const m = parseInt(getArg('--m'), 10);
const pubkeysArg = getArg('--pubkeys');

const NETWORKS = {
    zcash: bitgoLib.networks.zcash,
    bitcoinz: bitgoLib.networks.bitcoinz,
    litecoinz: bitgoLib.networks.litecoinz,
    zero: bitgoLib.networks.zero,
    zeroclassic: bitgoLib.networks.zeroclassic,
    zclassic: bitgoLib.networks.zclassic,
    gemlink: bitgoLib.networks.gemlink,
    ycash: bitgoLib.networks.ycash,
    flux: bitgoLib.networks.flux
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

Generate multisig (P2SH) address:
  wallet-cli --network <network> --gen-multisig --m <required> --pubkeys <pubkey1,pubkey2,...>

Derive address from WIF:
  wallet-cli --network <network> --address-from-wif --wif <private-key-wif>

SINGLE-SIG TRANSACTION
----------------------
Build and sign a transaction in one step:
  wallet-cli --network <network> \\
    --create-signed \\
    --wif <private-key-wif> \\
    --to <recipient-address> \\
    --amount <satoshis> \\
    --fee <satoshis> \\
    (--utxos '<json>' | --utxos-file <file>) \\
    [--blockheight <height>]

MULTISIG TRANSACTIONS
---------------------

1) Create unsigned transaction (no private key needed):
  wallet-cli --network <network> \\
    --create-unsigned \\
    --redeem-script <hex> \\
    (--utxos '<json>' | --utxos-file <file>) \\
    --to <recipient-address> \\
    --amount <satoshis> \\
    [--fee <satoshis>] \\
    [--blockheight <height>]

2) Add partial signature to unsigned tx:
  wallet-cli --network <network> \\
    --sign \\
    --rawtx <hex> \\
    --redeem-script <hex> \\
    --wif <your-wif> \\
    (--utxos '<json>' | --utxos-file <file>)

3) Finalize a partially-signed transaction:
  wallet-cli --network <network> \\
    --finalize \\
    --rawtx <hex> \\
    --redeem-script <hex> \\
    --wif <final-signer-wif> \\
    (--utxos '<json>' | --utxo-file <file>)
    

OPTIONS
-------
--network <name>        Network to use (default: bitcoinz)
--gen-address           Generate a new address
--gen-multisig          Generate a multisig address (P2SH)
--address-from-wif      Derive address from WIF
--uncompressed          Generate uncompressed public key

--wif <wif>             Sender private key (WIF) — required for signing
--to <address>          Recipient address
--amount <satoshis>     Amount to send (in satoshis)
--fee <satoshis>        Transaction fee (default: 2000)
--utxos <json>          UTXOs as JSON string
--utxos-file <file>     UTXOs from JSON file
--blockheight <height>  Current block height (expiry = +300)
--rawtx <hex>           Raw transaction hex (for --sign or --finalize)
--redeem-script <hex>   Redeem script for multisig transactions
--m <number>            Required signatures for multisig
--pubkeys <hex,...>     Comma-separated public keys for multisig

--create-unsigned       Build an unsigned multisig transaction
--create-signed         Build and sign a transaction in one step (requires --wif)
--sign                  Add partial signature to an unsigned transaction
--finalize              Finalize a partially-signed transaction

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

if (generateMultisig) {
    if (!m || !pubkeysArg) {
        console.error('Missing --m or --pubkeys argument for multisig generation.');
        process.exit(1);
    }

    const pubkeysHex = pubkeysArg.split(',').map(k => k.trim());
    const pubKeysBuffers = pubkeysHex.map(hex => Buffer.from(hex, 'hex'));

    if (m > pubKeysBuffers.length) {
        console.error(`M (${m}) cannot be greater than the number of public keys (${pubKeysBuffers.length})`);
        process.exit(1);
    }

    try {
        const redeemScript = bitgoLib.script.multisig.output.encode(m, pubKeysBuffers);

        const scriptPubKey = bitgoLib.script.scriptHash.output.encode(bitgoLib.crypto.hash160(redeemScript));
        const address = bitgoLib.address.fromOutputScript(scriptPubKey, network);

        console.log(JSON.stringify({
            network: networkName,
            address,
            m,
            n: pubKeysBuffers.length,
            redeemScript: redeemScript.toString('hex'),
            pubkeys: pubkeysHex
        }, null, 2));

        process.exit(0);

    } catch (err) {
        console.error('Failed to generate multisig address:', err.message);
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


if (createSigned) {
    if (!senderWif || !recipientAddress || !amountToSend || (!utxoDataString && !utxoFilePath)) {
        console.error('Missing required arguments for --create-signed. Need --wif, --to, --amount, --utxos/--utxos-file');
        process.exit(1);
    }

    try {
        const utxos = loadUtxos(utxoDataString, utxoFilePath);
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
        process.exit(0);

    } catch (error) {
        console.error('Failed to create signed transaction:', error.message);
        process.exit(1);
    }
}


if (createUnsigned) {
    if (!recipientAddress || !amountToSend || (!utxoDataString && !utxoFilePath) || !redeemScriptHex) {
        console.error('Missing required arguments for --create-unsigned. Need --to, --amount, --utxos/--utxos-file, --redeem-script');
        process.exit(1);
    }

    try {
        const utxos = loadUtxos(utxoDataString, utxoFilePath);
        const redeemScript = Buffer.from(redeemScriptHex, 'hex');

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
            const scriptPubKey = bitgoLib.script.scriptHash.output.encode(bitgoLib.crypto.hash160(redeemScript));
            const changeAddress = bitgoLib.address.fromOutputScript(scriptPubKey, network);
            txb.addOutput(changeAddress, changeAmount);
        }

        const tx = txb.buildIncomplete();
        console.log(tx.toHex());
        process.exit(0);

    } catch (err) {
        console.error('Failed to create unsigned transaction:', err.message);
        process.exit(1);
    }
}


if (signPartial) {
    if (!rawTxHex || !senderWif || !redeemScriptHex || (!utxoDataString && !utxoFilePath)) {
        console.error('Missing required arguments for --sign. Need --rawtx, --wif, --redeem-script, --utxos/--utxos-file');
        process.exit(1);
    }

    try {
        const utxos = loadUtxos(utxoDataString, utxoFilePath);
        const redeemScript = Buffer.from(redeemScriptHex, 'hex');
        const keyPair = bitgoLib.ECPair.fromWIF(senderWif, network);

        const tx = bitgoLib.Transaction.fromHex(rawTxHex, network);
        const txb = bitgoLib.TransactionBuilder.fromTransaction(tx, network);

        for (let i = 0; i < utxos.length; i++) {
            txb.sign(i, keyPair, redeemScript, bitgoLib.Transaction.SIGHASH_ALL, utxos[i].value);
        }

        const partiallySignedTx = txb.buildIncomplete();
        console.log(partiallySignedTx.toHex());
        process.exit(0);

    } catch (err) {
        console.error('Failed to sign transaction:', err.message);
        process.exit(1);
    }
}

if (finalizeTx) {
    if (!rawTxHex || !senderWif || !redeemScriptHex || (!utxoDataString && !utxoFilePath)) {
        console.error('Missing required arguments for --finalize. Need --rawtx, --wif, --redeem-script, --utxos/--utxos-file');
        process.exit(1);
    }

    try {
        const utxos = loadUtxos(utxoDataString, utxoFilePath);
        const redeemScript = Buffer.from(redeemScriptHex, 'hex');
        const keyPair = bitgoLib.ECPair.fromWIF(senderWif, network);

        const tx = bitgoLib.Transaction.fromHex(rawTxHex, network);
        const txb = bitgoLib.TransactionBuilder.fromTransaction(tx, network);

        for (let i = 0; i < utxos.length; i++) {
            txb.sign(i, keyPair, redeemScript, bitgoLib.Transaction.SIGHASH_ALL, utxos[i].value);
        }

        const finalizedTx = txb.build();
        console.log(finalizedTx.toHex());
        process.exit(0);

    } catch (err) {
        console.error('Failed to finalize transaction:', err.message);
        process.exit(1);
    }
}
