"""Check local-only routing and account migration using disposable Steam directories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "guest"))
from hd2_profile import remove_fx_launch_options


def config(options, appid="553850"):
    return '"UserLocalConfigStore"\n{\n "Software" { "Valve" { "Steam" { "apps" { "' + appid + '" {\n  "LaunchOptions" ' + json.dumps(options) + '\n } } } } }\n}\n'


class AccountOptionsTests(unittest.TestCase):
    def test_only_hd2_fx_options_are_removed(self):
        original = config('env FEX_DISKCACHE=0 %command% --use-d3d11')
        original += config('-novid', '440')
        updated, count = remove_fx_launch_options(original)
        self.assertEqual(count, 1)
        self.assertNotIn('FEX_DISKCACHE', updated)
        self.assertIn('-novid', updated)
        self.assertEqual(remove_fx_launch_options(updated), (updated, 0))

    def test_windows_options_and_other_fields_survive(self):
        original = config('-dx12')
        original += '\n"Other" { "LaunchOptions" "env FEX_DISKCACHE=0" }\n'
        self.assertEqual(remove_fx_launch_options(original), (original, 0))

    def test_escaped_paths_and_comments(self):
        original = '// A comment\n' + config('env PROTON_EAC_RUNTIME="$HOME/path with spaces" %command%')
        updated, count = remove_fx_launch_options(original)
        self.assertEqual(count, 1)
        self.assertTrue(updated.startswith('// A comment\n'))
        self.assertNotIn('LaunchOptions', updated)

    def test_invalid_config_is_rejected(self):
        for text in ('"x" { "y" "unterminated', '"x" { "y" "z"', '"x" }'):
            with self.assertRaises(ValueError):
                remove_fx_launch_options(text)


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.steam = self.root / 'Steam'
        self.tool = self.steam / 'steamapps/common/FEX-Emu'
        self.tool.mkdir(parents=True)
        self.launcher = self.tool / 'fex-compat-tool'
        self.original = ('#!' + sys.executable + '\nimport json,os,sys\n'
                         'keys=["FEX_NEEDSSECCOMP","FEX_DISKCACHE","PROTON_EAC_RUNTIME","WINEDEBUG"]\n'
                         'print(json.dumps({"args":sys.argv[1:],"env":{k:os.environ.get(k) for k in keys}}))\n')
        self.launcher.write_text(self.original)
        self.launcher.chmod(0o755)
        tools = self.root / 'tools'
        tools.mkdir()
        (tools / 'pgrep').write_text('#!/bin/sh\nexit 1\n')
        (tools / 'pgrep').chmod(0o755)
        self.env = dict(os.environ, STEAM_ROOT=str(self.steam), STATE_DIR=str(self.root / 'state'),
                        PATH=str(tools) + os.pathsep + os.environ['PATH'])
        for key in ('SteamAppId', 'SteamGameId', 'FEX_NEEDSSECCOMP', 'FEX_DISKCACHE', 'PROTON_EAC_RUNTIME', 'WINEDEBUG'):
            self.env.pop(key, None)

    def profile(self, action='install', renderer='dxmt'):
        result = subprocess.run([sys.executable, str(ROOT / 'guest/hd2_profile.py'), action, '--renderer', renderer],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def launch(self, appid, args=None, gameid=None):
        env = dict(self.env, SteamAppId=appid)
        if gameid is not None:
            env['SteamGameId'] = gameid
        args = args or ['waitforexitandrun', '--', '/path with spaces/proton', 'run', 'start_protected_game.exe']
        result = subprocess.run([str(self.launcher), *args], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_profile_applies_to_hd2_without_account_options(self):
        self.profile()
        result = self.launch('553850')
        self.assertEqual(result['env']['FEX_DISKCACHE'], '0')
        self.assertEqual(result['env']['FEX_NEEDSSECCOMP'], '1')
        self.assertIn('Proton EasyAntiCheat Runtime', result['env']['PROTON_EAC_RUNTIME'])
        self.assertEqual(result['args'][-1], '--use-d3d11')
        self.assertIn('/path with spaces/proton', result['args'])

    def test_other_games_pass_through_unchanged(self):
        self.profile()
        args = ['run', '--', '/other game.exe']
        result = self.launch('440', args)
        self.assertEqual(result['args'], args)
        self.assertTrue(all(value is None for value in result['env'].values()))

    def test_game_id_fallback_and_no_duplicate_dx11(self):
        self.profile()
        result = self.launch('0', ['run', '--', 'game.exe', '--use-d3d11'], gameid='553850')
        self.assertEqual(result['args'].count('--use-d3d11'), 1)
        self.assertEqual(result['env']['FEX_DISKCACHE'], '0')

    def test_vulkan_profile_uses_default_d3d12_arguments(self):
        self.profile(renderer='vulkan')
        result = self.launch('553850')
        self.assertNotIn('--use-d3d11', result['args'])
        self.assertEqual(result['env']['FEX_NEEDSSECCOMP'], '1')

    def test_directx_prerequisites_do_not_receive_game_flags(self):
        self.profile()
        args = ['run', '--', '/redist/DXSETUP.exe', '/silent']
        result = self.launch('553850', args)
        self.assertEqual(result['args'], args)

    def test_multiple_accounts_migrate_and_original_can_be_restored(self):
        accounts = []
        for name in ('cached-test', 'cached-main'):
            path = self.steam / 'userdata' / name / 'config/localconfig.vdf'
            path.parent.mkdir(parents=True)
            path.write_text(config('env FEX_NEEDSSECCOMP=1 %command%'))
            accounts.append(path)
        self.profile()
        self.profile()
        for path in accounts:
            self.assertNotIn('LaunchOptions', path.read_text())
        self.profile('restore')
        self.assertEqual(self.launcher.read_text(), self.original)
        self.assertFalse((self.tool / '.hd2-fx-original-launcher').exists())


if __name__ == '__main__':
    unittest.main()
