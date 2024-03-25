def find_duplicates(lst):
    seen = set()
    duplicates = set()
    for item in lst:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return duplicates


songs_list = []
duplicates = find_duplicates(songs_list)
print("Duplicate songs:", duplicates)