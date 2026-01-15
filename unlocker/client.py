import asyncio
import logging

import asyncssh

log = logging.getLogger('unlocker')


class TCPHandshakeProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        transport.close()


class ServerUnlocker:
    def __init__(self, servers):
        self.servers = servers

    async def run(self):
        tasks = [self.unlock_server(config) for config in self.servers]
        await asyncio.gather(*tasks)

    async def ssh_unlock(self, ssh_options, passphrase, server_name):
        log.debug('SSH connecting', extra={'server': server_name})
        async with asyncssh.connect(**ssh_options) as conn:
            log.info('Unlocking %s', server_name, extra={'server': server_name})
            try:
                await conn.run('cat > /lib/cryptsetup/passfifo', input=passphrase, check=True)
                log.info('Password written', extra={'server': server_name})
            except asyncssh.ProcessError as exc:
                log.warning('Password write failed: %s', exc.stderr.strip(), extra={'server': server_name})

    async def unlock_server(self, config):
        host, port = config.get('host'), config.getint('port')

        log.info('Starting unlocker loop', extra={'server': config.name})
        while True:
            try:
                loop = asyncio.get_running_loop()
                await asyncio.wait_for(loop.create_connection(TCPHandshakeProtocol, host, port), timeout=config.getint('connect_timeout', 10))

                ssh_options = {
                    'host': host,
                    'port': port,
                    'client_keys': [config.get('ssh_private_key')],
                    'username': config.get('username', 'root'),
                    'known_hosts': config.get('known_hosts'),
                    'passphrase': config.get('ssh_private_key_passphrase', None)
                }

                await asyncio.wait_for(self.ssh_unlock(ssh_options, passphrase=config.get('cryptsetup_passphrase'), server_name=config.name), timeout=config.getint('ssh_connect_timeout', 10))
            except ConnectionRefusedError:
                log.debug('Connection refused', extra={'server': config.name})
            except asyncio.TimeoutError:
                log.debug('Timeout error', extra={'server': config.name})
            except asyncssh.DisconnectError as exc:
                log.warning('Disconnect error: %s', exc, extra={'server': config.name})
            except OSError as exc:
                log.warning('Connection error: %s', exc, extra={'server': config.name})

            await asyncio.sleep(config.getint('sleep_interval', 2))
