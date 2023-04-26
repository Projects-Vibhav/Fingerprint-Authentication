from flask import Flask, render_template, request, send_from_directory, url_for
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from PIL import Image
import cv2
import mysql.connector
from io import BytesIO

def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

app = Flask(__name__)
app.config["SECRET_KEY"] = "abcd"
app.config["UPLOADED_PHOTOS_DEST"] = "uploads"

photos = UploadSet("photos", IMAGES)
configure_uploads(app, photos)

class UploadForm(FlaskForm):
    photo = FileField(
        validators = [
            FileAllowed(photos, "Only images are allowed"),
            FileRequired("File should not be empty")
        ]
    )
    submit = SubmitField("Upload")

@app.route("/uploads/<filename>")
def get_file(filename):
    return send_from_directory(app.config["UPLOADED_PHOTOS_DEST"], filename)


@app.route("/", methods = ["GET", "POST"])
def upload_image():
    form = UploadForm()
    if form.validate_on_submit():
        output = request.form.to_dict()
        name = output["candidate"]
        id = output["id"]
        print("Name:", name)
        print("ID:", id)
        filename = photos.save(form.photo.data)
        file_url = url_for("get_file", filename = filename)
        print(file_url)
        directory = r"path"
        test = cv2.imread(directory + file_url)
        print(test)
        mydb  = mysql.connector.connect(
            host = "localhost",
            user = "root",
            password = ""
        )
        cursor = mydb.cursor()
        cursor.execute("use voter")
        cursor.execute("select CAST(AES_DECRYPT(VoterName, 'secretkey') AS CHAR(255)), VoterID, Vote_Status, Fingerprint from voter_info where VoterID = " + str(id))
        arr = cursor.fetchall()
        print(arr[0][0])
        votername = arr[0][0]

        if arr[0][2] == 0:
            
            # real = cv2.imread(r"C:\Users\utkar\OneDrive\Desktop\test6.bmp")
            bytes_io = BytesIO(arr[0][3])
            real = Image.open(bytes_io)
            bitmap = real.convert('1')
            bitmap.save("real.bmp")

            real = cv2.imread(r"path")

            sift = (
                cv2.SIFT_create()
            )

            keypoints1, des1 = sift.detectAndCompute(test, None)
            keypoints2, des2 = sift.detectAndCompute(real, None)
            matches = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 10}, {}).knnMatch(des1, des2, k = 2)

            matchPoints = []
            for p, q in matches:
                if p.distance < 0.9 * q.distance or p.distance > 1.1 * q.distance:
                    matchPoints.append(p)

            keypoints = 0
            if len(keypoints1) <= len(keypoints2):
                keypoints = len(keypoints1)
            else:
                keypoints = len(keypoints2)

            best_score = 0
            print(len(matchPoints))
            if len(matchPoints) / keypoints * 100 > best_score:
                best_score = len(matchPoints) / keypoints * 100
                image = real
                kp1, kp2, mp = keypoints1, keypoints2, matchPoints

            print("Accuracy:", best_score)

            if len(matchPoints) > 0:
                result = cv2.drawMatches(test, kp1, image, kp2, mp, None)
                result = cv2.resize(result, None, fx = 2, fy = 2)
                # cv2.startWindowThread()
                # cv2.namedWindow("result")
                cv2.imshow("Result", result)
                cv2.waitKey(0)
                # cv2.destroyAllWindows()

            print(name)

            threshold = 35
            if(best_score > threshold):
                cursor.execute("UPDATE candidate_info SET votes_received = votes_received+1 WHERE CandidateName = " + '"' + name + '"' + ";")
                cursor.execute("UPDATE voter_info SET Vote_Status = 1 WHERE VoterID = " + str(id) + ";")
                mydb.commit()
                msg = None
            else:
                msg = "Authentication failed"

            # img = get_grayscale(img)
            # cv2.imshow("Result", img)
            # cv2.waitKey(0)
            # print(img)
            # cv2.imwrite(r"C:\Users\utkar\OneDrive\Desktop\stuff\Aikya\integrate\uploads" + "\\" + filename, img)
        else:
            msg = "You are not eligible to vote again"
    else:
        votername = None
        msg = None
    return render_template("front.html", form = form, votername = votername, msg = msg)


if __name__ == "__main__":
    app.run(debug = True, port = 1000)