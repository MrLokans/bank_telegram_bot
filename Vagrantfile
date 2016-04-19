VAGRANTFILE_API_VERSION = "2"
Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.ssh.insert_key = false
    config.vm.provider :virtualbox do |vb|
        vb.customize ["modifyvm", :id, "--memory", "512"]
    end
    
  config.vm.define "mrlokans" do |app|
    app.vm.hostname = "telegrambot.dev"
    app.vm.box = "centos/7"
    app.vm.network :private_network, ip: "192.168.120.120"
  end
end
