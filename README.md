# Ansible Base
Base ansible code containing modules/plugins/playbooks/vars/scripts and etc.

## Installation
Install ansible base required packages and tools


### Base installation
Install required packages and ansible itself.

Install following packages:
- wget
- curl
- python3
- python3-pip
- git-core
- openssl

Install ansible and required python packages using PIP.
make sure that your user local path is included in $PATH

```
sudo apt update -qq
sudo apt -qqqy install wget curl python3 python3-pip git-core openssl sshpass
python3 -m pip install -r requirement.txt
```

Ensure ~/.local/bin is in PATH
```
export PATH=$PATH:~/.local/bin
```

Clone this code.
```
git clone git@git.arexgo.com:ansible/base.git ~/ansible
cd ~/ansible
```

Make following file permissions and links
```
chmod +x $PWD/scripts/run-playbook
ln -fvs $PWD/scripts/run-playbook /usr/local/bin/run-playbook
chmod +x $PWD/scripts/check-secrets
ln -fvs $PWD/scripts/check-secrets /usr/local/bin/check-secrets
chmod +x $PWD/scripts/vault-action
ln -fvs $PWD/scripts/vault-action /usr/local/bin/vault-action
```
Ensure /usr/local/bin is in PATH
```
export PATH=$PATH:/usr/local/bin
```

Add following to ~/.bashrc or ~/.zshrc
```
alias check-playbook="run-playbook -C -D"
alias activate="source activate"
```

### OH-MY-ZSH
This part is required if you want to use auto-completion and extra tools.

Install zsh and oh-my-zsh
```
sudo apt -qqqy install zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

Make following links for oh-my-zsh
```
mkdir -p ~/.oh-my-zsh/completions
ln -svf $PWD/scripts/_activate.zsh ~/.oh-my-zsh/completions/_activate
ln -svf $PWD/scripts/_run-playbook.zsh ~/.oh-my-zsh/completions/_run-playbook
```

### Environment installation
This part is for downloaded required environments and roles.

Clone [https://git.arexgo.com/ansible/init](Ansible init) repository to init/arex.
```
git clone git@git.arexgo.com:ansible/init.git init/arex
```

Activate dummy env and run init play. And ensure dynamic inventory config.
```
source activate
ansible-playbook -e sub_path=arex/ src/playbooks/init.yml
ln -s $PWD/env/arex/prod/files/dynamic_inventory.cfg $PWD/env/arex/prod/inventory/dynamic-hosts/
```

Get Vault password from box and create vault password file.
```
cat > vault/arex.pass <<EOF
VAULT PASSPHRASE FROM BOX
EOF
```
Ensure following on ssh config file ~/.ssh/config
```
Host arex.jump
    Hostname JUMP_SERVER_IP
    Port JUMP_SERVER_PORT
    User JUMP_SERVER_USERNAME
    IdentityFile JUMP_SERVER_USER_KEY
```
### Test installation

Sample commands for testing the installation.
```
cd ~/ansible
ssh-add env/arex/prod/files/id_ansible
activate arex prod
# View current inventory graph
./scripts/inv-info --graph
# Test a ping command
check-playbook -p sysAdmin -t ping -T master_s1
```
