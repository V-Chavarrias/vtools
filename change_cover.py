import argparse
import os
from pptx import Presentation
from pptx.parts.image import Image


def parse_arguments():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description="Update the title, author, and cover image in PowerPoint files."
    )
    parser.add_argument(
        "--title",
        default="",
        help="New title; leave empty to keep the existing title.",
    )
    parser.add_argument(
        "--author",
        default="Victor Chavarrias\nWillem Ottevanger",
        help=r"New author; leave empty to keep the existing author. Use \n for line breaks.",
    )
    parser.add_argument(
        "--old-author",
        default="Victor",
        help="Text used to identify the existing author.",
    )
    parser.add_argument(
        "--image",
        default="",
        help="Path to the replacement image; leave empty to keep the existing image.",
    )
    parser.add_argument(
        "--input-dir",
        default=os.path.join(script_directory, "day4"),
        help="Directory containing the PowerPoint files.",
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(script_directory, "day4_modified"),
        help="Directory where modified files are written.",
    )
    return parser.parse_args()


def main():
    args = parse_arguments()
    new_title_text = args.title.replace(r"\n", "\n")
    new_author = args.author.replace(r"\n", "\n")
    old_author = args.old_author
    new_image = os.path.abspath(args.image) if args.image else ""
    directory = os.path.abspath(args.input_dir)
    output_directory = os.path.abspath(args.output_dir)

    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Input directory does not exist: {directory}")
    if new_image and not os.path.isfile(new_image):
        raise FileNotFoundError(f"Image file does not exist: {new_image}")

    os.makedirs(output_directory, exist_ok=True)

    processed_files = 0
    for filename in os.listdir(directory):
        if filename.startswith("~") or not filename.lower().endswith(".pptx"):
            continue

        ppt_path = os.path.join(directory, filename)
        prs = Presentation(ppt_path)

        first_slide = prs.slides[0]

        if new_title_text and first_slide.shapes.title:
            first_slide.shapes.title.text = new_title_text

        for shape in first_slide.shapes:
            if old_author and new_author and shape.has_text_frame and old_author in shape.text:
                alignment_old = shape.text_frame.paragraphs[0].alignment
                shape.text = new_author
                for paragraph in shape.text_frame.paragraphs:
                    paragraph.alignment = alignment_old

            if new_image and not shape.has_text_frame:
                image_rid = getattr(shape._element, "blip_rId", None)
                if image_rid:
                    slide_part = shape.part
                    image_part = slide_part.related_part(image_rid)
                    image_part.blob = Image.from_file(new_image)._blob

        prs.save(os.path.join(output_directory, filename))
        processed_files += 1

    print(f"Updated {processed_files} PowerPoint file(s).")


if __name__ == "__main__":
    main()