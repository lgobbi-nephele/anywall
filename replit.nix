{pkgs}: {
  deps = [
    pkgs.python311Packages.mysql-connector
    pkgs.mysql-shell-innovation
    pkgs.mysql-shell
    pkgs.mysql_jdbc
    pkgs.mysql84
  ];
}
