from extractor import parse_salary, parse_experience, clean_skill, experience_level


def test_parse_salary():
    assert parse_salary("15 - 25 trieu") == (15.0, 25.0)
    low, high = parse_salary("Thoa thuan", title="Junior Python Developer")
    assert low > 0 and high >= low
    low, high = parse_salary("Up to 2,000 USD")
    assert high == 50.0
    low, high = parse_salary("Luong: 20.000.000 - 30.000.000 VND")
    assert (low, high) == (20.0, 30.0)


def test_parse_experience():
    assert parse_experience("Khong yeu cau kinh nghiem") == 0
    assert parse_experience("Yeu cau 2 nam kinh nghiem") == 2
    assert parse_experience("Senior 5 nam kinh nghiem") == 5


def test_clean_skill():
    assert clean_skill("reactjs") == "React"
    assert clean_skill("nodejs") == "Node.js"
    assert clean_skill("python") == "Python"


def test_experience_level():
    assert experience_level(0) == "Entry"
    assert experience_level(2) == "Junior"
    assert experience_level(3) == "Middle"
    assert experience_level(6, title="Senior Developer") == "Senior"


def run():
    test_parse_salary()
    test_parse_experience()
    test_clean_skill()
    test_experience_level()
    print("Tat ca test da chay thanh cong")


if __name__ == "__main__":
    run()
