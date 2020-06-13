from os import scandir


def ls2(path):
    return [obj.name for obj in scandir(path) if obj.is_file()]

extension_file = '.wav'
files = ls2("audios/pending/")
for file in files:
    if (file.find(extension_file) != -1):
        name, extension = file.split('.')
        filename = 'audios/'+file
        print(name, extension, filename)


