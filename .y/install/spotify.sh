# https://www.spotify.com/us/download/linux/

# You will first need to configure our debian repository:

curl -sS https://download.spotify.com/debian/pubkey_6224F9941A8AA6D1.gpg | sudo gpg --dearmor --yes -o /etc/apt/trusted.gpg.d/spotify.gpg
echo "deb http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list

# Then you can install the Spotify client:

sudo apt-get update && sudo apt-get install spotify-client
