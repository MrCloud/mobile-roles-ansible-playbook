oh-my-zsh
=========

An Ansible role to install oh-my-zsh.

Requirements
------------

None.

Role Variables
--------------

- zsh_custom_dir: ~/.oh-my-zsh/custom
    - This variable is used in other roles which depend on this role.

- oh_my_zsh_theme: hnakamur
    - The theme

Dependencies
------------

None.

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role: hnakamur.oh-my-zsh, oh_my_zsh_theme: cloud }

License
-------

MIT

Author Information
------------------

[Hiroaki Nakamura]( http://hnakamur.github.io/ )
