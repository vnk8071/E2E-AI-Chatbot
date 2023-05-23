echo "Install poetry and packages"
curl -sSL https://install.python-poetry.org | python3 -
poetry shell
poetry install

echo "Start download GPT4All model"
dir="./models/"
if [[ ! -e $dir ]]; then
    mkdir $dir
elif [[ ! -d $dir ]]; then
    echo "$dir already exists but is not a directory" 1>&2
fi
wget https://gpt4all.io/models/ggml-gpt4all-j-v1.3-groovy.bin -P $dir
echo "Done download GPT4ALL in $dir"