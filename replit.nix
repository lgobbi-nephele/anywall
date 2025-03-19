{pkgs}: {
  deps = [
    pkgs.python39Full
    pkgs.libmysqlclient
    pkgs.python311Packages.mysql-connector
    pkgs.mysql-shell-innovation
    pkgs.mysql-shell
    pkgs.mysql_jdbc
    pkgs.mysql84
  ];
}
