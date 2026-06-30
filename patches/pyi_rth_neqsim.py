import sys, os, glob

if getattr(sys, 'frozen', False):
    java_home = os.environ.get('JAVA_HOME', '')
    if not (java_home and os.path.isdir(java_home)):
        for pattern in [
            r'C:\Program Files\Eclipse Adoptium\jdk-21*',
            r'C:\Program Files\Eclipse Adoptium\jdk-17*',
            r'C:\Program Files\Java\jdk-21*',
            r'C:\Program Files\Java\jdk-17*',
        ]:
            for m in glob.glob(pattern):
                if os.path.isdir(m) and os.path.isfile(os.path.join(m, 'bin', 'java.exe')):
                    os.environ['JAVA_HOME'] = m
                    java_home = m
                    break
            if java_home:
                break
