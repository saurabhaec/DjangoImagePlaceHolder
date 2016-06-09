from django.conf  import settings
settings.configure(
		ROOT_URLCONF = __name__,
		DEBUG=True, 
);
import sys
from django.conf.urls import url 
from django.http import HttpResponse
from django import forms
from PIL import Image, ImageDraw
from django.core.cache import cache
import hashlib
from django.views.decorators.http import etag
from io import BytesIO

class ImageForm(forms.Form):
	"""Form to validate requested placeholder image."""
	height = forms.IntegerField(min_value=1, max_value=2000)
	width = forms.IntegerField(min_value=1, max_value=2000)
	def generate(self, image_format='PNG'):
		"""Generate an image of the given type and return as raw bytes."""
		height = self.cleaned_data['height']
		width = self.cleaned_data['width']
		key = '{}.{}.{}'.format(width, height, image_format)
		content = cache.get(key)
		if content is None: 
			image = Image.new('RGB', (width, height))
			draw = ImageDraw.Draw(image)
			text = '{} X {}'.format(width, height)
			textwidth, textheight = draw.textsize(text)
			if textwidth < width and textheight < height:
				texttop = (height - textheight) // 2
				textleft = (width - textwidth) // 2
				draw.text((textleft, texttop), text, fill=(255, 255, 255))
			content = BytesIO()
			image.save(content, image_format)
			content.seek(0)
			cache.set(key, content, 60 * 60)
			
		return content 


def generate_etag(request, width, height):
	content = 'Placeholder: {0} x {1}'.format(width, height)
	return hashlib.sha1(content.encode('utf-8')).hexdigest()

@etag(generate_etag)
def placeholder(request, width, height):
	form = ImageForm({'height': height, 'width': width})
	if form.is_valid():
		image = form.generate()
		return HttpResponse(image, content_type='image/png')
	else:
		return HttpResponseBadRequest('Invalid Image Request')

	 
urlpatterns = (
	url(r'^image/(?P<width>[0-9]+)x(?P<height>[0-9]+)/$', placeholder, name='placeholder'),
) 
 
if __name__ == '__main__':
	from django.core.management import execute_from_command_line
	execute_from_command_line(sys.argv)
