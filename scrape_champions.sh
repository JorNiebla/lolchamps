#!/bin/bash

page=$(curl https://leagueoflegends.fandom.com/wiki/List_of_champions)
images=$(echo $page |
    grep -o -P "<tbody>.*?</tbody>" |
    grep -o -P "<img .*?>" | 
    grep "width=\"42\"" |
    sed "s/ //g" |
    sed "s/amp;//g" |
    sed "s/&#39;/'/g")
mkdir -p images
for image in $images; do
    image_url=$(echo $image | grep -o -P "https.*?.png")
    name=$(echo $image | grep -o -P "(?<=alt=\").*?(?=Original)")
    curl $image_url > images/$name.png 2> /dev/null &
done